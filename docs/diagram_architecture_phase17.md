# Diagram Architecture Phase 17

## Drafting And Annotation Standards

Phase 17 adds a controlled drafting layer for generated plant diagrams. The goal is to make PFD, BFD, P&ID-lite, and control exports behave like governed engineering drawings rather than untracked images.

## Implemented

- `DiagramSheet` now carries drafting metadata: drawing number, sheet number, revision, revision date, issue status, and prepared-by fields.
- `apply_diagram_drafting_metadata()` assigns deterministic drawing numbers and sheet counts using a diagram-specific prefix.
- BFD, PFD, P&ID-lite, and control diagram builders now attach drafting metadata to generated sheets.
- SVG rendering now includes a lower-right drafting title block with drawing, sheet, revision, status, date, and author fields.
- Draw.io export now inserts a title-block cell on every page so editable diagrams preserve the same drafting context.
- Regression coverage checks that drafting metadata appears in both SVG and Draw.io output.

## Design Notes

- The title block is intentionally small and placed at the lower-right corner to preserve the process area while keeping drawings reviewable.
- Drawing numbers are generated from clean uppercase prefixes such as `ROUTE-PFD-001`.
- Revision defaults are conservative: revision `A`, issue status `For Review`, prepared by `AoC`.
- Custom control-system SVG helpers already receive sheet metadata, but their bespoke renderer can be further tightened in a future phase if we want the exact same visible SVG title-block treatment across every specialized control sheet.

## Next Hardening Targets

- Add a shared title-block renderer for bespoke control SVG sheets.
- Add optional checker stamps, reviewer initials, and approval dates.
- Add validator rules for missing drawing numbers, duplicate sheet numbers, and inconsistent revision metadata.
- Add export metadata to reports so diagrams can be traced back to the source artifact and project configuration.
