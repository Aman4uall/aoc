# Phase B: Material and Energy Balance Full Parity

Status: complete

## Implemented in this slice
- Expanded material-balance chapter rendering with:
  - overall plant balance summary
  - section balance summary
  - reaction extent allocation
  - byproduct closure
  - unit packet balance summary
  - recycle and purge summary
  - composition closure summary
  - unitwise outlet composition snapshot
  - stream role summary
  - long stream ledger
  - stream-balance calculation traces
- Expanded energy-balance chapter rendering with:
  - overall energy summary
  - unit duty summary
  - section duty summary
  - unit thermal packet summary
  - recovery candidate summary
  - utility consumption basis
  - energy-balance calculation traces
- Added route-family-specific balance focus sections and pushed balance references into design chapters:
  - route-family stream focus in material balance
  - route-family duty focus in energy balance
  - route-family basis and balance reference snapshot in reactor design
  - route-family basis and balance reference snapshot in main process-unit design
- Added explicit local stream tables inside design chapters:
  - reactor feed / product / recycle summary
  - unit-by-unit feed / product / recycle summary for the main process-unit chapter
- Added benchmark-style local split and component-priority views:
  - reactor local stream split summary
  - key reactor component balance
  - process-unit local stream split summary
  - key process-unit component balance
- Tightened the report parity contract so Phase B chapter depth is now measured explicitly.

## Result
- Material-balance and energy-balance chapters now have a formal benchmark-style backbone.
- Reactor and main process-unit chapters now reuse local stream and duty context instead of reading as detached downstream summaries.
