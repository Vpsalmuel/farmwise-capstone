# FarmWise Agronomy Guide (Sample Knowledge Base)

This guide is the grounding source for the Crop Advisor agent. Every piece of advice given to a farmer must trace back to an entry below. If a problem doesn't match an entry, the agent should say so and escalate rather than guess.

---

## MAIZE (Corn)

### Issue: Yellowing leaves (lower leaves first)
- **Likely cause:** Nitrogen deficiency
- **Symptoms:** Older/lower leaves turn pale yellow starting from the tip, V-shaped yellowing along the midrib
- **Recommended action:** Apply nitrogen-rich fertilizer (e.g. urea) at recommended local rate; side-dress 4-6 weeks after planting
- **Severity:** Low — self-treatable
- **Escalate if:** Yellowing spreads rapidly across whole plant within days, or accompanied by stunted growth and wilting (may indicate maize streak virus)

### Issue: Yellowing + streaking pattern on leaves
- **Likely cause:** Maize Streak Virus (transmitted by leafhoppers)
- **Symptoms:** Pale yellow streaks running parallel to leaf veins, stunted growth, poor cob formation
- **Recommended action:** No cure once infected — remove and destroy infected plants to reduce spread
- **Severity:** High — outbreak risk
- **Escalate:** Yes — always escalate to extension officer for regional outbreak tracking

### Issue: Holes in leaves / chewed leaves with visible larvae
- **Likely cause:** Fall Armyworm
- **Symptoms:** Ragged holes, sawdust-like droppings in leaf whorl, visible caterpillars
- **Recommended action:** Handpick larvae in small farms; approved bio-pesticide (e.g. Bt-based) for larger infestation
- **Severity:** Medium
- **Escalate if:** Infestation covers more than 30% of the field

---

## CASSAVA

### Issue: Brown/black patches on leaves with mosaic-like mottling
- **Likely cause:** Cassava Mosaic Disease
- **Symptoms:** Mottled yellow-green leaf pattern, leaf distortion, reduced tuber size
- **Recommended action:** Use disease-free planting material (stem cuttings) for next planting; remove and burn infected plants
- **Severity:** High
- **Escalate:** Yes — spreads via whitefly and infected cuttings, needs regional monitoring

### Issue: Root rot / tubers rotting in ground
- **Likely cause:** Waterlogging or fungal root rot
- **Symptoms:** Soft, dark, foul-smelling tubers when harvested
- **Recommended action:** Improve field drainage; avoid planting in waterlogged soil; rotate crops next season
- **Severity:** Medium — self-treatable with drainage correction

---

## TOMATO

### Issue: Wilting despite adequate watering
- **Likely cause:** Bacterial wilt or Fusarium wilt
- **Symptoms:** Sudden wilting of whole plant, brown discoloration inside stem when cut
- **Recommended action:** Remove and destroy affected plants immediately; do not replant tomato/pepper family in same soil for 2-3 seasons
- **Severity:** High
- **Escalate:** Yes — soil-borne, can persist and spread

### Issue: Yellow leaves with tiny white insects underneath
- **Likely cause:** Whitefly infestation
- **Symptoms:** Sticky residue on leaves, yellowing, sooty mold growth
- **Recommended action:** Yellow sticky traps; neem-based spray; remove heavily infested leaves
- **Severity:** Low-Medium — self-treatable

### Issue: Dark sunken spots on fruit
- **Likely cause:** Blossom end rot (calcium deficiency) or Anthracnose (fungal)
- **Symptoms:** Sunken black/brown spots, often at fruit tip
- **Recommended action:** Ensure consistent watering (irregular watering worsens calcium uptake); for fungal spots, remove affected fruit and improve air circulation
- **Severity:** Low — self-treatable

---

## PEPPER (Chili/Bell)

### Issue: Curled, distorted young leaves
- **Likely cause:** Aphid infestation or viral infection (transmitted by aphids)
- **Symptoms:** New growth curls and twists, sticky residue, stunted plant
- **Recommended action:** Neem oil spray for aphids; if curling persists after treatment, may be viral — remove plant
- **Severity:** Medium

---

## RICE

### Issue: Yellow-orange leaves, stunted tillering
- **Likely cause:** Nitrogen deficiency or Rice Yellow Mottle Virus
- **Symptoms:** If uniform yellowing across field — likely nutrient deficiency. If mottled/patchy with stunting — viral
- **Recommended action:** For nutrient deficiency, apply nitrogen fertilizer. For suspected virus, no chemical cure — remove affected plants
- **Severity:** Medium-High depending on cause
- **Escalate if:** Mottled pattern with stunting present (viral suspected)

### Issue: White/grey lesions with brown borders on leaves
- **Likely cause:** Rice Blast (fungal)
- **Symptoms:** Diamond-shaped lesions, can spread to entire field rapidly in humid conditions
- **Recommended action:** Fungicide application at first sign; avoid excess nitrogen which worsens spread
- **Severity:** High
- **Escalate:** Yes — can devastate entire field within days

---

## YAM

### Issue: Tubers with dry rot / brown internal discoloration
- **Likely cause:** Yam dry rot (fungal, often from poor storage or infected planting material)
- **Symptoms:** Firm brown/black rot inside tuber, visible at cutting
- **Recommended action:** Use only healthy setts for planting; store harvested yams in cool, dry, ventilated conditions
- **Severity:** Medium — mostly a storage/prevention issue

---

## GENERAL ESCALATION RULE

Any of the following should ALWAYS be escalated to a human extension officer regardless of crop:
- Rapid spread across more than a third of the field within a few days
- Symptoms matching a known viral disease (no chemical cure exists)
- Farmer reports unusual/unfamiliar symptoms not matching any entry above
- Farmer describes livestock or human health symptoms alongside crop issues (out of scope — redirect to appropriate authority)

If the farmer's description is vague (e.g. "my crop is sick"), the agent must ask a clarifying follow-up (crop type, part of plant affected, how long observed) rather than guessing.
