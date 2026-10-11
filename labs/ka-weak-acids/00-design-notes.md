# Ka of Weak Acids at Home — Design Notes (brainstorm, 2026-10-11)

Status: brainstorm / feasibility. Not yet a student-facing procedure.

## Goal
Determine Ka (pKa) of two weak acids by titration with NaOH using only
grocery / pharmacy / hardware-store materials, with pH measured by
universal test strips (optionally red-cabbage indicator).

Candidate acids:
- Acetic acid — Heinz distilled white vinegar, "5% acidity" (~0.83 M). pKa(lit) = 4.76.
- Oxalic acid — Bar Keepers Friend powder (7.5–9.5 % w/w oxalic acid, rest feldspar
  abrasive + surfactant). pKa1 = 1.25, pKa2 = 4.27 (lit).

## Core method: half-equivalence
At half-equivalence [HA] = [A⁻], so pH = pKa (Henderson–Hasselbalch).

Why this is the right method for home:
1. NaOH concentration cancels. You only need the *equivalence volume* V_eq
   (found with a color indicator), then measure pH at V_eq/2.
   No standardization required for Ka itself.
2. The buffer region is flat, so a ±2 % error in volume barely moves pH.
3. The pH reading maps 1:1 onto pKa. Strip error of ±0.25 pH → pKa ±0.25
   → Ka within a factor of ~1.8. Compare: using initial pH of vinegar
   (Ka = [H+]²/C) doubles the exponent error → factor ~3 for the same strip error.

Improvement: measure at 1/4, 1/2, 3/4 of V_eq and compute
pKa = pH − log([A⁻]/[HA]) at each (ratios 1/3, 1, 3 → corrections +0.48, 0, −0.48).
Three estimates, averaged. Doubles as an H–H exercise.

## Titrant (NaOH) — source options, ranked
1. **Crystal drain opener, "100 % lye"** (Roebic Heavy Duty Crystal Drain Opener,
   Rooto, Instant Power Crystal Lye — hardware/farm store, ~$15 for 2 lb).
   Also food-grade lye (grocery canning/soap aisle in some stores, or online).
   Dissolve 4.0 g in water to 100 mL → ~1.0 M. (Add lye TO water; exothermic.)
   Caveats: hygroscopic + some Na2CO3 → weighed concentration good to ~±5 %.
   Fine for Ka (concentration cancels). Avoid Drano crystals (contain Al chips, NaNO3).
2. **Oven cleaner (Easy-Off HD, Goo Gone Oven & Grill, etc.)** — NOT recommended as titrant.
   SDS values for this product class are 1–5 % NaOH (≈0.25–1.25 M; exact % withheld
   as trade secret), plus monoethanolamine (a weak base, pKa 9.5, which buffers
   and smears the endpoint), surfactants (foam), thickeners, fragrance.
   Could not find an SDS for the Goo Gone oven product specifically. Pump/aerosol
   delivery is also hard to measure volumetrically.

Optional standardization (only needed for the "verify the 5 % label" extension):
- Cream of tartar (KHC4H4O6, 188.18 g/mol) — a recognized primary standard for bases.
  Low solubility (~0.5 g/100 mL cold) → titrate ~0.25 g in 50 mL warm water with
  NaOH diluted to ~0.1 M.
- Citric acid "sour salt" (anhydrous, 192.12 g/mol, triprotic) — more soluble,
  but anhydrous vs monohydrate ambiguity in some retail products.

## Analyte prep
Vinegar: use as-is, 5.00 mL sample (needs ~4.2 mL of 1 M NaOH). Or dilute
1:4 to lower ionic strength (see accuracy section) and use 20 mL.

Bar Keepers Friend: stir ~2 g powder into ~40 mL warm water for 5 min, let
feldspar settle, filter through a coffee filter. Filtrate ≈ 0.03–0.04 M oxalic
acid (unknown exactly — doesn't matter for Ka). Expect some foam from the
sulfonate surfactant. Only ~0.2 g of oxalic acid is extracted from 2 g; titrate
20 mL of filtrate with NaOH diluted to 0.1 M (≈ 6–7 mL to second equivalence).
Alternative purer source: hardware-store "wood bleach" / deck brightener
(oxalic acid dihydrate crystals, ~99 %), which also makes pKa1-from-initial-pH
possible if a meter is available.

## Indicator / endpoint
- Equivalence-point pH: acetate ~8.9–9.1; oxalate ~8.3–8.5.
- **Turmeric** (pinch in rubbing alcohol) transitions yellow → red-brown over
  pH ~7.4–8.6 — a decent phenolphthalein substitute, sharp enough since the
  pH jump at equivalence spans ~6 → 11 within a drop or two.
- Red cabbage: purple (~7) → blue (~8) → green (~9–10). Workable; endpoint =
  first stable blue/teal. Broader and more subjective than turmeric.
- Strips: do NOT dip strips in the titration beaker (dye bleeds). Transfer a
  drop onto the strip with a toothpick/clean dropper.

## Delivering the titrant without a burette
- 10 mL oral-medication syringe (pharmacy, free/cheap), 0.2 mL graduations.
  Resolution ~0.1 mL on ~4 mL → ~2 %. A 1 mL or 3 mL syringe for the last drops.
- Better: **gravimetric titration** — put titrant in a dropper bottle, weigh on
  a 0.01 g jewelry scale before/after. 0.01 g on 4 g = 0.25 %. Scales are ~$10.
- Drop counting (~20 drops/mL) as a fallback; calibrate drops per mL first.

## Accuracy budget (honest expectation)
| Component | Universal strips (1.0 steps) | Narrow-range strips (0.5/0.25 steps) | $15 pen meter, 2-pt cal |
|---|---|---|---|
| pH reading | ±0.5 | ±0.25 | ±0.05–0.1 |
| pKa (acetic, lit 4.76) | 4.3–5.3 | 4.5–5.0 | 4.6–4.8 |
| Ka error factor | ~3× | ~1.8× | ~1.25× |
| Can distinguish acetic (4.76) from oxalic pKa2 (4.27)? | No | Marginal | Yes |

Ionic-strength note: at I ≈ 0.4 M (undiluted vinegar half-titrated) the
*measured* pH at half-equivalence ≈ 4.6, not 4.76 (activity of acetate).
Diluting the vinegar 1:4 brings it to ≈ 4.65. Mention as a "why is it low"
discussion point, or ignore at strip-level precision.

## Oxalic acid specifics
- pKa1 = 1.25 is NOT measurable by titration here: the first equivalence
  (pH ≈ 2.7) is not a visible jump because pKa1 and pKa2 differ by only ~3 and
  the acid is nearly strong at the start. The curve looks like a one-step
  titration with a long buffer plateau. Good discussion content.
- pKa2 from the pH at 3/4 of the *total* (second) equivalence volume, where
  [HC2O4⁻] = [C2O4²⁻]. Expect measured ≈ 4.1–4.2.
- Extension (meter + weighed wood-bleach oxalic acid of known molarity):
  Ka1 from initial pH via the quadratic. Strips can't do pH 1.3.

## Home-made reference buffers (to calibrate strips / meter)
All three are NIST standard buffers made from grocery/hardware items:
- Saturated cream of tartar (KHT) at 25 °C → pH 3.557
- 0.01 M borax (20 Mule Team, 3.81 g/L) → pH 9.18
- 0.025 M NaHCO3 + 0.025 M Na2CO3 (baking soda 2.10 g/L + washing soda 2.65 g/L) → pH 10.01
Use these to build a "known-pH color key" for the strips/cabbage and
correct for strip bias. This turns strip readings from ±0.5 toward ±0.25.

## Safety
- 1 M NaOH: goggles mandatory, gloves, plastic or glass only (no aluminum).
  Add lye to water, never the reverse. Vinegar neutralizes spills on skin/surfaces.
- Oxalic acid: toxic if ingested (kidney), skin/eye irritant. BKF is sold as a
  cleanser; wood bleach crystals more so — keep away from food prep areas.
- Turmeric stains; cabbage juice is harmless.

## Open questions / decisions for the lab author
1. Keep BKF (fun extraction step, "pure grocery") or switch to wood bleach
   (cleaner data, enables Ka1 extension)? Or offer both.
2. Is the ~0.5 pKa gap between acetic and oxalic-pKa2 enough of a contrast,
   given strip resolution? Alternatives with bigger contrast: aspirin
   (pharmacy, pKa 3.5, monoprotic, classic lab but low solubility/binders),
   phosphoric acid from rust remover (pKa2 7.2, very distinguishable),
   citric acid (sour salt, pKa 3.1/4.8/6.4 — overlapping, messy).
3. Recommend the $10–15 pen meter as "strongly recommended optional"?
4. Volumetric (syringe) vs gravimetric (scale) titrant delivery as the
   default procedure.
