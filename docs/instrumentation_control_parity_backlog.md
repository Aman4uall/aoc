## Phase H: Instrumentation & Process Control Parity

Status:
- complete

Acceptance reached:
- the `instrumentation_control` chapter now includes control philosophy, control architecture decision, objective and disturbance coverage, startup/shutdown/override logic, alarm/interlock basis, utility-linked control basis, and loop sheets
- control loops now carry deterministic unit-level metadata for objective, disturbance, startup logic, shutdown logic, override basis, safeguard linkage, and criticality
- control-plan validation now warns if objective, startup/shutdown logic, or override basis disappears from emitted loops

Current delivered sections:
- `### Control Philosophy`
- `### Control Architecture Decision`
- `### Loop Objective Matrix`
- `### Controlled and Manipulated Variable Register`
- `### Startup, Shutdown, and Override Basis`
- `### Alarm and Interlock Basis`
- `### Utility-Integrated Control Basis`
- `### Control Loop Sheets`

Benchmark-parity outcome:
- the chapter now reads like a real process-control chapter with loop sheets and operating logic rather than only a short regulatory-loop list

Next report-completion move:
1. close Phase I HAZOP to benchmark depth with fuller node-by-node tables and safeguard/recommendation structure
2. then close Phase J SHE
3. then close Phase K layout
4. then move to project-cost and finance presentation parity
