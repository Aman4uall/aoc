## Phase 16: Domain Packs

Phase 16 starts by adding a domain-pack layer above the generic target profile and template library.

### What Phase 16 Adds

- a first-class domain-pack artifact:
  - `diagram_domain_packs`
- reusable pack definitions for:
  - `specialty_chemicals`
  - `petrochemicals`
  - `utility_dense_process`
- per-pack defaults for:
  - required BFD sections
  - expected PFD unit families
  - major stream roles
  - preferred template families
  - equipment template overrides
  - allowed PFD symbol policy
  - sheet-density budgets
  - connector-lane spacing
  - row-width packing budgets

### Current Integration

The first Phase 16 slice now feeds domain-pack data into:

- `build_diagram_target_profile(...)`
- target-profile `domain_pack_id`
- pack-specific section and stream-role expectations
- pack-specific main-body PFD density limits
- pack-aware template preference ordering for ambiguous unit selection
- pack-specific equipment template overrides
- pack-specific allowed PFD symbol policy
- pack-aware target/semantics validation warnings
- pack-aware symbol-policy drift validation
- pack-aware PFD connector lane spacing
- pack-aware PFD sheet packing width
- pipeline persistence through `diagram_domain_packs.json`

### Why This Matters

Before this step, every plant family used one generic diagram target profile.

Now we have:

- a clean place to encode family-specific diagram defaults
- a safer path for differing process patterns without branching the whole renderer
- a base for future domain-tuned templates, routing, and validation policies

### Boundary After This Step

Phase 16 still does **not** yet include:

- full pack-specific symbol libraries beyond allowed-symbol policy
- deeper pack-specific validators beyond target-envelope and symbol-policy checks
- richer pack-specific routing policies beyond spacing/density controls
- extensive equipment-template packs for solids/pharma/domain-specific unit variants

Those are the next natural Phase 16 follow-up steps.
