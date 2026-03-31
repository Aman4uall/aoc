## Material Balance

### Overall Plant Balance Summary

| Basis | Mass Flow (kg/h) | Molar Flow (kmol/h) |
| --- | --- | --- |
| Fresh feed | 25952.368 | 837.633819 |
| External outlet | 25952.368 | 432.910401 |
| Recycle circulation | 27585.316 | 492.451084 |
| Side draws | 0.000 | 0.000000 |
| Closure error (%) | 0.000 | - |

### Section Balance Summary

| Section | Label | Type | Inlet kg/h | Outlet kg/h | Side Draw kg/h | Recycle kg/h | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| feed_handling | Feed handling | feed_preparation | 26953.864 | 26953.864 | 0.000 | 0.000 | converged |
| reaction | Reaction | reaction | 26953.864 | 26953.863 | 0.000 | 0.000 | converged |
| primary_recovery | Primary recovery | primary_recovery | 26953.863 | 26559.945 | 0.000 | 0.000 | converged |
| recycle_recovery_carbonate_loop_cleanup | Carbonate loop cleanup | recycle_recovery | 25582.324 | 26583.820 | 0.000 | 26583.820 | estimated |
| purification | Purification | purification | 26583.820 | 25976.243 | 0.000 | 1001.496 | estimated |

### Reaction Extent Allocation

| Extent | Kind | Representative Component | Fraction of Converted Feed | Status |
| --- | --- | --- | --- | --- |
| omega_catalytic_main_extent | main | Ethylene glycol | 0.990000 | converged |
| omega_catalytic_side_extent_1 | byproduct | Trace heavy glycols | 0.010000 | estimated |

### Byproduct Closure

| Component | Basis | Allocation Fraction | Provenance | Status |
| --- | --- | --- | --- | --- |
| Trace heavy glycols | Declared route byproducts | 1.000000 | declared_trace | estimated |

### Unit Packet Balance Summary

| Unit | Type | Service | Inlet Streams | Outlet Streams | Inlet kg/h | Outlet kg/h | Closure Error (%) | Status | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| feed_prep | feed_preparation | Feed preparation | S-101, S-102, S-401 | S-150 | 26953.864 | 26953.864 | 0.000 | converged | complete |
| primary_flash | flash | Primary flash and vent recovery | S-201 | S-202, S-203 | 26953.863 | 26953.863 | 0.000 | converged | complete |
| purification | distillation | Purification train | S-301 | S-401, S-402, S-403 | 26583.820 | 26583.820 | 0.000 | converged | partial |
| reactor | reactor | Reaction zone | S-150 | S-201 | 26953.864 | 26953.863 | 0.000 | converged | complete |
| recycle_recovery | recycle | Recycle recovery | S-203 | S-301 | 25582.324 | 26583.820 | 3.767 | estimated | partial |

### Recycle and Purge Summary

| Loop | Source Unit | Target Unit | Recycle Streams | Purge Streams | Max Error (%) | Mean Error (%) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| recycle_recovery_recycle_loop | recycle_recovery | purification | S-301 | - | 0.100 | 0.100 | converged |
| purification_recycle_loop | purification | feed_prep | S-401 | S-403 | 8.650 | 4.004 | estimated |

### Composition Closure Summary

| Unit | Reactive | Inlet Fraction Sum | Outlet Fraction Sum | New Components | Missing Components | Error (%) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| feed_prep | no | 1.0000 | 1.0000 | - | - | 0.000 | converged |
| primary_flash | no | 1.0000 | 1.0000 | - | - | 0.000 | converged |
| purification | no | 1.0000 | 1.0000 | - | Trace heavy glycols | 0.000 | estimated |
| reactor | yes | 1.0000 | 1.0000 | Ethylene glycol, Trace heavy glycols | - | 0.000 | converged |
| recycle_recovery | no | 1.0000 | 1.0000 | - | - | 0.000 | converged |

### Unitwise Outlet Composition Snapshot

| Unit | Type | Inlet Phase | Outlet Phase | Outlet Mass Fractions | Status |
| --- | --- | --- | --- | --- | --- |
| feed_prep | feed_preparation | gas | gas | Ethylene oxide=0.700, Water=0.300 | converged |
| primary_flash | flash | gas | gas | Ethylene oxide=0.028, Trace heavy glycols=0.010, Water=0.011, Ethylene glycol=0.951 | converged |
| purification | distillation | gas | gas | Ethylene oxide=0.018, Water=0.020, Ethylene glycol=0.961 | estimated |
| reactor | reactor | gas | gas | Ethylene glycol=0.937, Ethylene oxide=0.028, Trace heavy glycols=0.009, Water=0.026 | converged |
| recycle_recovery | recycle | gas | gas | Ethylene glycol=0.950, Ethylene oxide=0.020, Trace heavy glycols=0.009, Water=0.021 | converged |

### Stream Role Summary

| Stream | Role | Section | From | To | kg/h | kmol/h |
| --- | --- | --- | --- | --- | --- | --- |
| S-101 | feed | feed_handling | battery_limits | feed_prep | 18378.663 | 417.222770 |
| S-102 | feed | feed_handling | battery_limits | feed_prep | 7573.705 | 420.411049 |
| S-150 | intermediate | reaction | feed_prep | reactor | 26953.864 | 877.547235 |
| S-201 | intermediate | reaction | reactor | primary_flash | 26953.863 | 465.036538 |
| S-202 | vent | primary_recovery | primary_flash | waste_treatment | 977.621 | 30.546176 |
| S-203 | intermediate | primary_recovery | primary_flash | recycle_recovery | 25582.324 | 412.624251 |
| S-301 | recycle | recycle_recovery_carbonate_loop_cleanup | recycle_recovery | purification | 26583.820 | 452.537668 |
| S-401 | recycle | purification | purification | feed_prep | 1001.496 | 39.913416 |
| S-402 | product | purification | purification | storage | 24974.747 | 402.364225 |
| S-403 | waste | purification | purification | waste_treatment | 0.000 | 0.000000 |

### Route-Family Stream Focus

| Stream | Role | From | To | Phase | kg/h | Dominant Components |
| --- | --- | --- | --- | --- | --- | --- |
| S-101 | feed | battery_limits | feed_prep | gas | 18378.663 | Ethylene oxide=18378.7 |
| S-102 | feed | battery_limits | feed_prep | gas | 7573.705 | Water=7573.7 |
| S-150 | intermediate | feed_prep | reactor | gas | 26953.864 | Ethylene oxide=18856.6, Water=8097.3 |
| S-201 | intermediate | reactor | primary_flash | gas | 26953.863 | Ethylene glycol=25252.5, Ethylene oxide=754.3, Water=694.1, Trace heavy glycols=253.0 |
| S-202 | vent | primary_flash | waste_treatment | gas | 977.621 | Ethylene oxide=709.0, Water=258.5, Trace heavy glycols=10.1 |
| S-203 | intermediate | primary_flash | recycle_recovery | gas | 25582.324 | Ethylene glycol=25252.5, Trace heavy glycols=242.9, Ethylene oxide=45.3, Water=41.6 |
| S-301 | recycle | recycle_recovery | purification | gas | 26583.820 | Ethylene glycol=25252.5, Water=565.2, Ethylene oxide=523.2, Trace heavy glycols=242.9 |
| S-401 | recycle | purification | feed_prep | gas | 1001.496 | Water=523.6, Ethylene oxide=477.9 |
| S-402 | product | purification | storage | gas | 24974.747 | Ethylene glycol=24974.7 |
| S-403 | waste | purification | waste_treatment | mixed | 0.000 | - |

### Long Stream Ledger

| Stream | Description | From | To | Component | kg/h | kmol/h | T (C) | P (bar) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S-101 | Ethylene oxide fresh feed | battery_limits | feed_prep | Ethylene oxide | 18378.663 | 417.222770 | 25.0 | 18.00 |
| S-102 | Water fresh feed | battery_limits | feed_prep | Water | 7573.705 | 420.411049 | 25.0 | 18.00 |
| S-150 | Mixed reactor feed | feed_prep | reactor | Ethylene oxide | 18856.564 | 428.071822 | 225.0 | 18.00 |
| S-150 | Mixed reactor feed | feed_prep | reactor | Water | 8097.300 | 449.475413 | 225.0 | 18.00 |
| S-201 | Reactor effluent | reactor | primary_flash | Ethylene glycol | 25252.525 | 406.839460 | 240.0 | 18.00 |
| S-201 | Reactor effluent | reactor | primary_flash | Ethylene oxide | 754.263 | 17.122873 | 240.0 | 18.00 |
| S-201 | Reactor effluent | reactor | primary_flash | Trace heavy glycols | 253.021 | 2.547741 | 240.0 | 18.00 |
| S-201 | Reactor effluent | reactor | primary_flash | Water | 694.054 | 38.526464 | 240.0 | 18.00 |
| S-202 | Primary separation overhead / vent / purge | primary_flash | waste_treatment | Ethylene oxide | 709.007 | 16.095501 | 205.0 | 16.50 |
| S-202 | Primary separation overhead / vent / purge | primary_flash | waste_treatment | Trace heavy glycols | 10.121 | 0.101910 | 205.0 | 16.50 |
| S-202 | Primary separation overhead / vent / purge | primary_flash | waste_treatment | Water | 258.493 | 14.348765 | 205.0 | 16.50 |
| S-203 | Primary separation bottoms / rich liquid | primary_flash | recycle_recovery | Ethylene glycol | 25252.525 | 406.839460 | 230.0 | 17.20 |
| S-203 | Primary separation bottoms / rich liquid | primary_flash | recycle_recovery | Ethylene oxide | 45.256 | 1.027372 | 230.0 | 17.20 |
| S-203 | Primary separation bottoms / rich liquid | primary_flash | recycle_recovery | Trace heavy glycols | 242.900 | 2.445831 | 230.0 | 17.20 |
| S-203 | Primary separation bottoms / rich liquid | primary_flash | recycle_recovery | Water | 41.643 | 2.311588 | 230.0 | 17.20 |
| S-301 | Cleanup / recycle recovery stream | recycle_recovery | purification | Ethylene glycol | 25252.525 | 406.839460 | 215.0 | 17.00 |
| S-301 | Cleanup / recycle recovery stream | recycle_recovery | purification | Ethylene oxide | 523.157 | 11.876425 | 215.0 | 17.00 |
| S-301 | Cleanup / recycle recovery stream | recycle_recovery | purification | Trace heavy glycols | 242.900 | 2.445831 | 215.0 | 17.00 |
| S-301 | Cleanup / recycle recovery stream | recycle_recovery | purification | Water | 565.238 | 31.375952 | 215.0 | 17.00 |
| S-401 | Light ends / recoverable recycle | purification | feed_prep | Ethylene oxide | 477.901 | 10.849052 | 45.0 | 1.00 |
| S-401 | Light ends / recoverable recycle | purification | feed_prep | Water | 523.595 | 29.064364 | 45.0 | 1.00 |
| S-402 | On-spec product | purification | storage | Ethylene glycol | 24974.747 | 402.364225 | 45.0 | 1.10 |

### Stream-Balance Calculation Traces

| Trace | Formula | Inputs | Result | Notes |
| --- | --- | --- | --- | --- |
| Main reaction extent | extent = product_kmol / nu_product | product_kmol=406.839460; nu_product=1.000 | 406.839460 kmol/h | - |
| Feed extent with conversion/selectivity | feed_extent = (product_kmol / nu_product) / (selectivity * conversion) | selectivity=0.9900; conversion=0.9600 | 428.071822 kmol/h | - |
| Byproduct closure allocation | Residual byproduct mass is allocated across explicit byproduct-closure estimates | closure_status=estimated; estimate_count=1; residual_mass_kg_hr=253.021 | 1 estimates items | This replaces the older implicit heavy-ends fallback whenever the reaction system carries a byproduct-closure artifact. |
| Multi-component recycle solution | Solve recycle per reactant using target_total, consumed, recovery, and purge fractions | Ethylene oxide=fresh=417.223; recycle=10.849; total=428.072; Water=fresh=420.411; recycle=29.064; total=449.475 | 2 components solved components | This is the first generic convergence slice: reactants are solved through the same recycle/purge loop instead of family-specific inline math. |
| Unit-sequence expansion | stream_count = feeds + mixed feed + reactor + separation + recycle + product/waste | family=generic | 10 streams | - |
| Fresh-feed to external-out closure | closure = |fresh_feed - external_out| / fresh_feed | fresh_feed=25952.368; external_out=25952.368 | 0.000000 % | - |