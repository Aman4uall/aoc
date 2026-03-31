# Phase C: Deep Unit Design Parity

Status: complete

What this phase covers:
- deepen the dedicated reactor chapter toward benchmark-style calculation density
- deepen the dedicated main separation-unit chapter toward benchmark-style derivation density
- keep chapter parity measurable through explicit required markers

Implemented in this slice:
- reactor chapter now renders:
  - `Reactor Design Inputs`
  - `Reactor Operating Envelope`
  - `Reaction and Sizing Derivation Basis`
  - `Reactor Equation-Substitution Sheet`
  - `Reactor Geometry and Internals`
  - `Thermal Stability and Hazard Envelope`
  - `Integrated Utility Package Basis`
- main process-unit chapter now renders:
  - `Separation Design Inputs`
  - `Feed and Internal Flow Derivation`
  - `Column Operating Envelope`
  - `Reboiler and Condenser Package Basis`
  - `Heat-Transfer Package Inputs`
  - `Exchanger Package Selection Basis`
- absorber and crystallizer services now also expose a more explicit operating-envelope section
- report parity contract now checks the new Phase C chapter markers directly

Implemented in the current continuation slice:
- reactor chapter now includes explicit substitution-style checks for residence time, Damkohler basis, thermal intensity, heat-transfer area, heat-removal margin, and residual utility demand
- absorber-led services now include `Absorber Equation-Substitution Basis`
- solids-led services now include `Crystallizer / Filter / Dryer Equation-Substitution Basis`
- chapter tests now assert the worked-equation sections directly

Implemented in the latest distillation continuation slice:
- main distillation service now includes:
  - `Distillation Equation-Substitution Basis`
  - `Feed Condition and Internal Flow Substitution Sheet`
  - `Reboiler and Condenser Thermal Substitution Sheet`
- the main-column chapter now renders explicit Fenske / Underwood / Gilliland-style screening substitutions
- feed-condition, internal-flow, and reboiler/condenser thermal substitutions are now shown directly in the chapter instead of staying implicit inside traces only

Implemented in the current package-density continuation slice:
- absorber-led services now include equipment-level `Absorber Package Sizing Derivation`
- solids-led services now include equipment-level `Solids Package Sizing Derivation`
- the equipment sizing chapter now renders:
  - `Storage Transfer Pump Basis`
  - `Major Process Equipment Basis`
  - `Utility-Coupled Package Inventory`
  - `Equipment-by-Equipment Sizing Summary`
- report parity now checks the equipment sizing chapter for these benchmark-style section markers

Why this slice:
- the benchmark report does not just summarize reactor and column outputs; it walks through design inputs, internal-flow basis, thermal basis, and package basis in separate sections
- this slice makes the generated report read much closer to that structure without changing the solved kernel underneath

Completed in the final continuation slice:
- package-level derivation density was pushed into the equipment datasheet bundle
- datasheets now include `Package Derivation Basis` and `Mechanical Basis` sections for the major process equipment and utility-coupled packages
- absorber-led and solids-led package derivations are now visible both in the equipment sizing chapter and in the datasheet appendix path

Phase C acceptance reached:
- reactor chapter now has benchmark-style design-input, operating-envelope, derivation, substitution, geometry, hazard, and utility-package sections
- main separation chapter now has benchmark-style distillation / absorber / solids derivation density instead of summary-only rendering
- the equipment sizing chapter now behaves like a true extension of the unit-design chapters rather than a flat inventory list
- report parity checks and regression tests cover the critical Phase C chapter markers directly
