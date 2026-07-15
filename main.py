"""
FarmWise - Crop & Market Advisor for Smallholder Farmers
FastAPI wrapper around the CrewAI multi-agent system.

Flow: guard input -> run crew -> guard output -> human-in-the-loop check -> log
"""

import os
import re
import json
import logging
from datetime import datetime

import litellm
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM

# ---------------------------------------------------------------------------
# Patch: strip CrewAI's internal cache_breakpoint marker before it reaches
# Groq's API (Groq rejects the unknown field). See conversation history for
# root cause - CrewAI tags messages for prompt-caching, and not every
# provider path strips the tag before sending the request.
# ---------------------------------------------------------------------------
_original_completion = litellm.completion


def _patched_completion(*args, **kwargs):
    messages = kwargs.get("messages")
    if messages:
        for m in messages:
            if isinstance(m, dict):
                m.pop("cache_breakpoint", None)
    return _original_completion(*args, **kwargs)


litellm.completion = _patched_completion

# ---------------------------------------------------------------------------
# Logging (guardrail 4)
# ---------------------------------------------------------------------------
logger = logging.getLogger("farmwise")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_handler = logging.FileHandler("farmwise_log.jsonl")
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)


def log_query(crop, location, description, result, escalated, blocked):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "crop": crop,
        "location": location,
        "description": description,
        "escalated": escalated,
        "blocked": blocked,
        "result_summary": result[:300] if result else None,
    }
    logger.info(json.dumps(entry))
    return entry


# ---------------------------------------------------------------------------
# Load local knowledge base
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "agronomy_guide.md")) as f:
    AGRONOMY_GUIDE = f.read()

with open(os.path.join(BASE_DIR, "market_prices.csv")) as f:
    MARKET_PRICES = f.read()


# ---------------------------------------------------------------------------
# Guardrails (Week 9): input validation, grounding, human-in-the-loop
# ---------------------------------------------------------------------------
def validate_input(crop: str, location: str, description: str):
    """Returns (is_valid, error_message_or_None)."""
    if not description or len(description.strip()) < 5:
        return False, "Description is too short or empty. Please describe what you are seeing on your crop."

    if not crop or len(crop.strip()) < 2:
        return False, "Please tell us which crop this is about."

    suspicious_patterns = [
        r"ignore (all|previous) instructions",
        r"system prompt",
        r"you are now",
        r"</?script>",
        r"DROP TABLE",
        r"act as (?!a farmer)",
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            return False, "Your input could not be processed. Please describe your crop problem in plain language."

    return True, None


def check_grounding(advice_text: str, guide_text: str) -> bool:
    """Lightweight grounding check: does the advice reference known agronomy guide terms?"""
    guide_terms = set(re.findall(r"[A-Za-z]{4,}", guide_text.lower()))
    advice_terms = set(re.findall(r"[A-Za-z]{4,}", advice_text.lower()))
    overlap = guide_terms & advice_terms
    return len(overlap) >= 3


ESCALATION_KEYWORDS = [
    "outbreak", "mosaic", "streak virus", "blast", "wilt", "rapid spread",
    "whole field", "unfamiliar", "never seen", "spreading fast"
]


def needs_escalation(description: str, advice_text: str) -> bool:
    combined = (description + " " + advice_text).lower()
    return any(keyword in combined for keyword in ESCALATION_KEYWORDS)


# ---------------------------------------------------------------------------
# Agents (CrewAI) - created once at startup, reused across requests
# ---------------------------------------------------------------------------
llm = LLM(
    model="openai/llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
    temperature=0.3,
)

crop_advisor = Agent(
    role="Crop Advisor",
    goal=(
        "Interpret the farmer's description of their crop problem and identify the most likely "
        "issue using ONLY the provided agronomy guide. Never invent treatments not in the guide."
    ),
    backstory=(
        "You are an agronomy expert who has worked with smallholder farmers across West Africa "
        "for over a decade. You are careful, practical, and always ground your advice in the "
        "reference guide provided to you rather than guessing. When something does not clearly "
        "match a known issue, you say so honestly instead of inventing an answer."
    ),
    llm=llm,
    verbose=True,
)

market_analyst = Agent(
    role="Market Analyst",
    goal=(
        "Advise the farmer on selling timing and a fair price range for their crop, using ONLY "
        "the provided market price table."
    ),
    backstory=(
        "You are a market analyst who tracks local crop prices across regional markets. You give "
        "farmers realistic price ranges and honest timing advice (hold vs sell now), always noting "
        "that real prices vary by region and week."
    ),
    llm=llm,
    verbose=True,
)

action_recommender = Agent(
    role="Action Recommender",
    goal=(
        "Combine the Crop Advisor's diagnosis and the Market Analyst's guidance into one clear, "
        "practical next step for the farmer. Escalate to a human extension officer instead of "
        "recommending self-treatment whenever the issue looks serious or unfamiliar."
    ),
    backstory=(
        "You are the farmer's trusted point of contact who turns technical advice into a single, "
        "clear action. You are conservative about risk: if there is any doubt about a serious "
        "disease or outbreak, you recommend escalation to a human officer rather than a home remedy."
    ),
    llm=llm,
    verbose=True,
)


def build_crew(crop: str, location: str, description: str):
    diagnose_task = Task(
        description=(
            f'A farmer in {location} growing {crop} reports: "{description}".\n\n'
            f"Using ONLY this agronomy guide, identify the most likely issue, its severity, "
            f"and whether it should be escalated:\n\n{{agronomy_guide}}"
        ),
        expected_output="A short diagnosis: likely issue, severity (low/medium/high), and whether escalation is needed.",
        agent=crop_advisor,
    )

    market_task = Task(
        description=(
            f"The crop in question is {crop}. Using ONLY this market price table, give the farmer "
            f"a fair price range and timing advice (sell now vs hold):\n\n{{market_prices}}"
        ),
        expected_output="A short market note: price range and clear timing advice.",
        agent=market_analyst,
    )

    action_task = Task(
        description=(
            "Combine the crop diagnosis and market advice into ONE clear recommended next step "
            "for the farmer. If the diagnosis flagged escalation, the action MUST be to contact "
            "a local extension officer - do not suggest self-treatment in that case."
        ),
        expected_output=(
            "A JSON object with keys: diagnosis, market_note, recommended_action, escalate (true/false)."
        ),
        agent=action_recommender,
        context=[diagnose_task, market_task],
    )

    return Crew(
        agents=[crop_advisor, market_analyst, action_recommender],
        tasks=[diagnose_task, market_task, action_task],
        process=Process.sequential,
        verbose=True,
    )


async def run_farmwise(crop: str, location: str, description: str):
    # --- Guard input ---
    is_valid, error = validate_input(crop, location, description)
    if not is_valid:
        log_query(crop, location, description, result=None, escalated=False, blocked=True)
        return {"status": "blocked", "message": error}

    # --- Run crew ---
    crew = build_crew(crop, location, description)
    raw_result = await crew.kickoff_async(inputs={
        "agronomy_guide": AGRONOMY_GUIDE,
        "market_prices": MARKET_PRICES,
    })
    result_text = str(raw_result)

    # --- Guard output: grounding check ---
    is_grounded = check_grounding(result_text, AGRONOMY_GUIDE)
    if not is_grounded:
        log_query(crop, location, description, result=result_text, escalated=False, blocked=True)
        return {
            "status": "blocked",
            "message": "Advice could not be verified against the agronomy guide. Please try rephrasing your problem or contact a local extension officer.",
        }

    # --- Human-in-the-loop check ---
    escalate = needs_escalation(description, result_text)

    # --- Log ---
    log_query(crop, location, description, result=result_text, escalated=escalate, blocked=False)

    return {
        "status": "escalated" if escalate else "ok",
        "result": result_text,
        "escalate": escalate,
    }


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="FarmWise")


class AgentRunRequest(BaseModel):
    crop: str
    location: str
    description: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/agent/run")
async def agent_run(request: AgentRunRequest):
    result = await run_farmwise(request.crop, request.location, request.description)
    return JSONResponse(content=result)


@app.get("/", response_class=HTMLResponse)
def form():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FarmWise</title>
<style>
  body { font-family: -apple-system, sans-serif; background: #0f1b13; color: #eaf5ec; margin: 0; padding: 20px; }
  h1 { color: #7ec98f; font-size: 1.5rem; }
  form { max-width: 480px; margin: 0 auto; }
  label { display: block; margin-top: 16px; font-size: 0.9rem; color: #b7d6bd; }
  input, textarea { width: 100%; padding: 10px; margin-top: 6px; border-radius: 8px; border: 1px solid #2a3d2f; background: #16241a; color: #eaf5ec; font-size: 1rem; box-sizing: border-box; }
  button { margin-top: 20px; width: 100%; padding: 12px; background: #3f8f57; color: white; border: none; border-radius: 8px; font-size: 1rem; }
  #result { max-width: 480px; margin: 24px auto 0; padding: 16px; border-radius: 8px; background: #16241a; white-space: pre-wrap; display: none; }
  .escalate { border: 1px solid #d98c3d; }
  .blocked { border: 1px solid #c0392b; }
</style>
</head>
<body>
  <form id="farmwiseForm">
    <h1>FarmWise</h1>
    <label>Crop</label>
    <input type="text" id="crop" placeholder="e.g. Maize" required>
    <label>Location</label>
    <input type="text" id="location" placeholder="e.g. Kaduna" required>
    <label>Describe the problem</label>
    <textarea id="description" rows="4" placeholder="e.g. My maize leaves are yellowing from the bottom" required></textarea>
    <button type="submit">Get Advice</button>
  </form>
  <div id="result"></div>

<script>
document.getElementById('farmwiseForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const resultDiv = document.getElementById('result');
  resultDiv.style.display = 'block';
  resultDiv.className = '';
  resultDiv.textContent = 'Thinking...';

  const payload = {
    crop: document.getElementById('crop').value,
    location: document.getElementById('location').value,
    description: document.getElementById('description').value,
  };

  try {
    const res = await fetch('/agent/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.status === 'blocked') {
      resultDiv.className = 'blocked';
      resultDiv.textContent = data.message;
    } else if (data.status === 'escalated') {
      resultDiv.className = 'escalate';
      resultDiv.textContent = '⚠️ Escalated to extension officer\\n\\n' + data.result;
    } else {
      resultDiv.textContent = data.result;
    }
  } catch (err) {
    resultDiv.className = 'blocked';
    resultDiv.textContent = 'Something went wrong. Please try again.';
  }
});
</script>
</body>
</html>
"""
