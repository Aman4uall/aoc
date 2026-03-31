## Process Description

Solver-derived process description for route `omega_catalytic` built from `5` solved unit packets.

### Unit Sequence

| Unit | Type | Service | Inlet Streams | Outlet Streams | Closure | Coverage |
| --- | --- | --- | --- | --- | --- | --- |
| feed_prep | feed_preparation | Feed preparation | S-101, S-102, S-401 | S-150 | converged | complete |
| reactor | reactor | Reaction zone | S-150 | S-201 | converged | complete |
| primary_flash | flash | Primary flash and purge recovery | S-201 | S-202, S-203 | converged | complete |
| waste_treatment | waste_handling | Waste treatment | S-202, S-403 | - | converged | partial |
| recycle_recovery | recycle | Recycle recovery | S-203 | S-301 | estimated | partial |
| purification | distillation | Purification train | S-301 | S-401, S-402, S-403 | converged | partial |
| storage | storage | Product storage | S-402 | - | converged | partial |

### Section Topology

| Section | Label | Type | Units | Inlet Streams | Outlet Streams | Side Draws | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| feed_handling | Feed handling | feed_preparation | feed_prep | S-101, S-102, S-401 | S-150 | - | converged |
| reaction | Reaction | reaction | reactor | S-150 | S-201 | - | converged |
| primary_recovery | Primary recovery | primary_recovery | primary_flash | S-201 | S-202, S-203 | - | converged |
| recycle_recovery_carbonate_loop_cleanup | Carbonate loop cleanup | recycle_recovery | recycle_recovery | S-203 | S-301 | - | estimated |
| purification | Purification | purification | purification | S-301 | S-401, S-402, S-403 | - | estimated |

### Separation Architecture

| Separation | Family | Driving Force | Product Streams | Recycle Streams | Status |
| --- | --- | --- | --- | --- | --- |
| primary_flash_separation_packet | flash | temperature/volatility | S-203 | - | converged |
| purification_separation_packet | distillation | temperature/volatility | S-402 | S-401 | converged |

### Recycle Architecture

| Loop | Source Unit | Recycle Streams | Purge Streams | Status |
| --- | --- | --- | --- | --- |
| recycle_recovery_recycle_loop | recycle_recovery | S-301 | - | converged |
| purification_recycle_loop | purification | S-401 | S-403 | estimated |

### Unit Narrative

- `feed_prep`: Feed preparation. Inlet streams `S-101, S-102, S-401` and outlet streams `S-150` with `converged` closure and `complete` coverage.
- `reactor`: Reaction zone. Inlet streams `S-150` and outlet streams `S-201` with `converged` closure and `complete` coverage.
- `primary_flash`: Primary flash and purge recovery. Inlet streams `S-201` and outlet streams `S-202, S-203` with `converged` closure and `complete` coverage.
- `waste_treatment`: Waste treatment. Inlet streams `S-202, S-403` and outlet streams `-` with `converged` closure and `partial` coverage.
- `recycle_recovery`: Recycle recovery. Inlet streams `S-203` and outlet streams `S-301` with `estimated` closure and `partial` coverage.
- `purification`: Purification train. Inlet streams `S-301` and outlet streams `S-401, S-402, S-403` with `converged` closure and `partial` coverage.
- `storage`: Product storage. Inlet streams `S-402` and outlet streams `-` with `converged` closure and `partial` coverage.