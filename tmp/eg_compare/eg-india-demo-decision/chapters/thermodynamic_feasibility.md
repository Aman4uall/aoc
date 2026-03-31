## Thermodynamic Feasibility

### Selected Property Basis

Use cited public anchors with library-backed calculation and benchmark seeds for missing constants. selected for the active component set of route omega_catalytic.

| Property Basis | Feasible | Score |
| --- | --- | --- |
| direct_public_package | no | 16.00 |
| hybrid_cited_plus_library | yes | 62.00 |
| estimation_dominant | yes | 40.00 |
| analogy_basis | yes | 10.00 |

### Separation Thermodynamics Basis

| Component | Ttop (C) | Gamma top | Ktop | Method | Tbottom (C) | Gamma bottom | Kbottom | Method |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ethylene Glycol | 108.0 | 1.0000 | 0.0160 | ideal_raoult_missing_bip_clausius_clapeyron | 203.3 | 1.0000 | 0.3669 | ideal_raoult_missing_bip_clausius_clapeyron |
| Ethylene oxide | 108.0 | 1.0000 | 4.5086 | ideal_raoult_clausius_clapeyron | 203.3 | 1.0000 | 21.3927 | ideal_raoult_clausius_clapeyron |
| Water | 108.0 | 1.0000 | 0.4138 | ideal_raoult_missing_bip_antoine_extrapolated | 203.3 | 1.0000 | 5.2836 | ideal_raoult_missing_bip_antoine_extrapolated |

Light key: `Water`
Heavy key: `Ethylene Glycol`
Activity model: `ideal_raoult_missing_bip_fallback`
Average relative volatility: `19.3148`
System pressure: `3.240` bar

Fallback notes:
- Binary interaction parameters for Water / Ethylene Glycol were not resolved from cited/public sources.
- Activity coefficients defaulted to gamma=1.0 and the separation basis fell back to ideal Raoult's law for the key pair.

### Selected Thermodynamic Method

Use direct public property and reaction data where available. selected as the primary thermodynamic basis.

| Method | Feasible | Score | Rejected Reasons |
| --- | --- | --- | --- |
| direct_public_data | yes | 91.10 | - |
| correlation_interpolation | yes | 88.10 | - |
| estimation_method | yes | 65.90 | - |
| analogy_basis | yes | 53.50 | - |

### Thermodynamic Interpretation

The selected reaction is treated as thermodynamically favorable, with a negative Gibbs free energy and exothermic heat release that supports conversion but requires controlled heat removal.