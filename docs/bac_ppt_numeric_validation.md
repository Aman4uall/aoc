# BAC PPT Numeric Validation

This note records the Phase 5 numeric checks for the BAC PPT build.

Goal:
- confirm internal consistency of the curated slide numbers
- identify rounding changes needed for presentation
- flag values that are numerically consistent but presentation-risky

## 1. Validation Outcome Summary

| Validation Area | Status | Notes |
| --- | --- | --- |
| Capacity and throughput consistency | Pass | 50,000 TPA matches the sold-solution rate almost exactly |
| Revenue consistency | Pass | Revenue matches annual production x selling price exactly |
| Utility annualization consistency | Pass | Steam, cooling water, and electricity annual values reconcile with hourly loads |
| CAPEX / funding closure | Pass | Total project funding closes as CAPEX + working capital + IDC |
| Working-capital closure | Pass with explanation | Subcomponents are internally consistent but use different bases for different buckets |
| Reactor sizing arithmetic | Pass | Reactor volume, residence time, and heat density are consistent |
| Reactor basis consistency | Warning | Narrative and artifact wording still differ |
| Economics credibility for presentation | Warning | Payback, margin, NPV, and IRR are very strong and need cautious framing |

## 2. Core Arithmetic Checks

### 2.1 Capacity and Throughput

Inputs:
- annual production = 50,000,000 kg/y
- operating days = 330 d/y
- sold solution rate = 6,313.13 kg/h

Check:
- annualized production from hourly rate = `6,313.13 x 330 x 24 = 49,999,989.6 kg/y`

Result:
- error vs stated annual production = `-0.00002%`

Conclusion:
- production basis is internally consistent

### 2.2 Active Basis Check

Inputs:
- sold solution rate = 6,313.13 kg/h
- active basis = 3,156.57 kg/h

Check:
- active fraction = `3,156.57 / 6,313.13 = 0.5000008`

Conclusion:
- active basis is consistent with the 50 wt% commercial product basis

### 2.3 Revenue Check

Inputs:
- annual production = 50,000,000 kg/y
- selling price = INR 360/kg

Check:
- annual revenue = `50,000,000 x 360 = INR 18,000,000,000`

Conclusion:
- revenue is exactly consistent with production and price assumptions

## 3. Reactor and Utility Checks

### 3.1 Reactor Volumetric Throughput

Inputs:
- design volume = 123.76 m3
- residence time = 25.0 h

Check:
- volumetric throughput = `123.76 / 25 = 4.9504 m3/h`

Conclusion:
- reactor volume and residence time are internally consistent

### 3.2 Reactor Heat Density

Inputs:
- heat duty = 257.116 kW
- reactor volume = 123.76 m3

Check:
- heat release density = `257.116 / 123.76 = 2.078 kW/m3`

Conclusion:
- matches the reported reactor design basis

### 3.3 Utility Annualization

| Utility | Hourly Load | Annualized from Load | Reported Annualized | Status |
| --- | --- | --- | --- | --- |
| Steam | 2,277.136 kg/h | 18,034,917.12 kg/y | 18,034,917.1 kg/y | Pass |
| Cooling water | 107.593 m3/h | 852,136.56 m3/y | 852,136.6 m3/y | Pass |
| Electricity | 151.556 kW | 1,200,323.52 kWh/y | 1,200,323.5 kWh/y | Pass |

Conclusion:
- annual utility values are presentation-safe and numerically consistent

## 4. Cost and Funding Checks

### 4.1 OPEX Structure

| Item | Value | Share of OPEX |
| --- | --- | --- |
| Raw materials | INR 5,865,876,513.63/y | 95.49% |
| Utilities | INR 49,484,847.46/y | 0.81% |
| Labor | INR 156,000,000.00/y | 2.54% |
| Maintenance | INR 35,350,344.91/y | 0.58% |

Conclusion:
- percentages match the total OPEX basis
- the cost structure is highly raw-material dominated, which is plausible for a sold-solution specialty chemical case

### 4.2 Unit Cost Check

Inputs:
- annual OPEX = INR 6,143,068,271.54/y
- annual production = 50,000,000 kg/y

Check:
- unit production cost = `6,143,068,271.54 / 50,000,000 = INR 122.86/kg`

Conclusion:
- cost of production is internally consistent

### 4.3 CAPEX and Funding Closure

Inputs:
- total CAPEX = INR 1,259,334,185.14
- working capital = INR 2,046,225,419.05
- IDC = INR 19,292,439.51
- total project funding = INR 3,324,852,043.70

Check:
- CAPEX + WC + IDC = `1,259,334,185.14 + 2,046,225,419.05 + 19,292,439.51`
- result = `INR 3,324,852,043.70`

Conclusion:
- funding closure is exact

## 5. Working-Capital Checks

### 5.1 What Reconciles Cleanly

| Component | Basis | Check Result |
| --- | --- | --- |
| Product inventory | revenue x days | matches exactly |
| Receivables | revenue x days | matches exactly |
| Cash buffer | OPEX x days | matches exactly |

### 5.2 What Needs Explanation

| Component | Observation | Interpretation |
| --- | --- | --- |
| Raw-material inventory | does not equal total OPEX x 16.9 days | likely based on raw-material cost, not total OPEX |
| Payables | does not equal total OPEX x 24 days | likely based on payable-eligible purchase streams, not total OPEX |

Conclusion:
- working capital is not inconsistent
- but the slide should not imply that all WC buckets were generated from one single common base

Presentation recommendation:
- present working capital as a modeled cash-cycle result, not as a simplified one-line formula

## 6. Financial Feasibility Risk Review

### 6.1 Mathematically Consistent But Presentation-Risky Outputs

| Metric | Reported Value | Risk |
| --- | --- | --- |
| Gross margin | 65.87% | looks very high for a feasibility slide unless well contextualized |
| Payback | 0.48 y | likely to trigger skepticism if shown without qualification |
| NPV | 4,366.57 Cr INR | very large relative to CAPEX |
| IRR | 60.00% | unusually strong headline number |
| Minimum DSCR | 25.53 | indicates very easy debt service under current assumptions |

### 6.2 Why This Is A Presentation Risk

These values may still be model-consistent, but in an academic PPT they can look overstated if presented without caveats because:
- route remains feasibility-grade rather than bankable detailed design
- reactor and purification assumptions still contain unresolved basis simplifications
- selling price basis is very favorable relative to the modeled production cost
- current model likely reflects a screening economics posture rather than conservative project finance

### 6.3 Recommended Framing

Use wording such as:
- "model-based feasibility indicators"
- "screening-level economic results"
- "subject to route, purification, and market-price assumptions"

Avoid wording such as:
- "guaranteed profitability"
- "highly bankable case"
- "commercially proven final economics"

## 7. Payback Interpretation Warning

The deck currently carries:
- payback = `0.48 y`

However:
- a simple `CAPEX / gross profit` style check gives a much shorter value of about `0.11 y`

Interpretation:
- the reported payback clearly comes from the model's multi-period funding and cash-flow structure, not from a naive gross-profit shortcut

Presentation rule:
- if payback is shown, it must be labeled as `model-derived payback`
- do not verbally derive it from simple gross margin during the presentation unless the financial model basis is also explained

## 8. Recommended Slide-Safe Numbers

These are the preferred rounded values for visible slides.

| Metric | Slide Value |
| --- | --- |
| Capacity | 50,000 TPA |
| Sold solution rate | 6,313.13 kg/h |
| Active rate | 3,156.57 kg/h |
| Reactor volume | 123.76 m3 |
| Reactor duty | 257.12 kW |
| Storage tank volume | 1,969.85 m3 |
| Pump flow | 219.85 m3/h |
| Pump power | 36.58 kW |
| Total CAPEX | 125.93 Cr INR |
| Annual OPEX | 614.31 Cr INR/y |
| Working capital | 204.62 Cr INR |
| Annual revenue | 1,800.00 Cr INR/y |
| Payback | 0.48 y |
| IRR | 60.00% |
| Break-even capacity | 34.10% |

## 9. Values That Need Caution Notes In Slides Or Speaker Notes

| Value | Caution Needed |
| --- | --- |
| Payback = 0.48 y | label as model-derived |
| IRR = 60.00% | label as screening-level result |
| NPV = 4,366.57 Cr INR | label as highly assumption-sensitive |
| Reactor cost family basis | legacy vessel pricing note remains |
| Route selected | retain feasibility-grade language |

## 10. Final Phase 5 Recommendation

Numeric status before slide drafting:
- proceed with the curated values
- retain current rounded figures
- add caution language to economics slides
- do not simplify working capital into a single formula on slides
- keep reactor-basis reconciliation visible until final deck drafting

