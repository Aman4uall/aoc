from __future__ import annotations

from aoc.models import (
    BenchmarkManifest,
    ChapterArtifact,
    ChapterParityResult,
    DecisionAcceptanceResult,
    ReportChapterContract,
    ReportAcceptanceArtifact,
    ReportAcceptanceStatus,
    ReportParityArtifact,
    ReportParityFrameworkArtifact,
    ReportParityStatus,
    ReportSupportContract,
    RunStatus,
    SupportParityResult,
    ValidationIssue,
)


_CHAPTER_LIBRARY: dict[str, ReportChapterContract] = {
    "executive_summary": ReportChapterContract(
        chapter_id="executive_summary",
        benchmark_title="Executive Summary",
        notes="Benchmark report includes a standalone executive summary chapter.",
    ),
    "introduction_product_profile": ReportChapterContract(
        chapter_id="introduction_product_profile",
        benchmark_title="Introduction",
        required_markers=["Properties"],
        notes="Benchmark introduction includes identity and physical-property tables.",
    ),
    "literature_survey": ReportChapterContract(
        chapter_id="literature_survey",
        benchmark_title="Literature Survey",
        notes="Benchmark report includes a standalone literature survey chapter.",
    ),
    "market_capacity_selection": ReportChapterContract(
        chapter_id="market_capacity_selection",
        benchmark_title="Capacity Selection",
        notes="Current report structure carries market and capacity basis as a dedicated chapter even though the benchmark PDF folds it into surrounding sections.",
    ),
    "process_selection": ReportChapterContract(
        chapter_id="process_selection",
        benchmark_title="Process Selection",
        required_markers=["Route"],
        notes="Benchmark report includes process-route comparison and selection rationale.",
    ),
    "site_selection": ReportChapterContract(
        chapter_id="site_selection",
        benchmark_title="Site Selection",
        required_markers=["India"],
        notes="Benchmark report includes site-factor and India location rationale.",
    ),
    "thermodynamic_feasibility": ReportChapterContract(
        chapter_id="thermodynamic_feasibility",
        benchmark_title="Thermodynamics of Reaction",
        required_markers=["### Separation Thermodynamics Basis"],
        notes="Benchmark report contains dedicated thermodynamic basis and reaction feasibility discussion.",
    ),
    "reaction_kinetics": ReportChapterContract(
        chapter_id="reaction_kinetics",
        benchmark_title="Kinetics of Reaction",
        notes="Benchmark report contains a dedicated kinetics chapter.",
    ),
    "block_flow_diagram": ReportChapterContract(
        chapter_id="block_flow_diagram",
        benchmark_title="Block Diagram",
        required_markers=["### Diagram Basis", "### Diagram Acceptance"],
        notes="Benchmark report includes a standalone process block diagram.",
    ),
    "process_flow_diagram": ReportChapterContract(
        chapter_id="process_flow_diagram",
        benchmark_title="Process Flow Diagram",
        required_markers=["### Diagram Basis", "### Diagram Acceptance"],
        notes="Benchmark report may include an equipment-level process flow diagram supporting the design chapters.",
    ),
    "process_description": ReportChapterContract(
        chapter_id="process_description",
        benchmark_title="Process Description",
        required_markers=["### Unit Sequence", "### Recycle Architecture"],
        notes="Benchmark report includes a long narrative process description.",
    ),
    "material_balance": ReportChapterContract(
        chapter_id="material_balance",
        benchmark_title="Material Balance",
        required_outputs=["stream_table"],
        required_markers=[
            "### Overall Plant Balance Summary",
            "### Section Balance Summary",
            "### Unit Packet Balance Summary",
            "### Long Stream Ledger",
        ],
        notes="Benchmark report includes long unitwise stream tables.",
    ),
    "energy_balance": ReportChapterContract(
        chapter_id="energy_balance",
        benchmark_title="Energy Balance",
        required_outputs=["energy_balance"],
        required_markers=[
            "### Overall Energy Summary",
            "### Section Duty Summary",
            "### Unit Thermal Packet Summary",
            "### Utility Consumption Basis",
        ],
        notes="Benchmark report includes long unitwise energy-balance tables.",
    ),
    "heat_integration_strategy": ReportChapterContract(
        chapter_id="heat_integration_strategy",
        benchmark_title="Heat Integration Strategy",
        required_outputs=["heat_integration_study"],
        notes="Current report structure carries heat integration as a dedicated chapter-equivalent engineering section.",
    ),
    "reactor_design": ReportChapterContract(
        chapter_id="reactor_design",
        benchmark_title="Process Design of Main Reactor",
        required_outputs=["reactor_design"],
        required_markers=[
            "### Governing Equations",
            "### Reactor Design Inputs",
            "### Reaction and Sizing Derivation Basis",
            "### Reactor Equation-Substitution Sheet",
            "### Heat-Transfer Derivation Basis",
            "### Thermal Stability and Hazard Envelope",
            "### Reactor Feed / Product / Recycle Summary",
            "### Key Reactor Component Balance",
        ],
        notes="Benchmark report contains a dedicated deep reactor-design chapter.",
    ),
    "distillation_design": ReportChapterContract(
        chapter_id="distillation_design",
        benchmark_title="Process Design of Main Separation Unit",
        required_outputs=["column_design"],
        required_markers=[
            "### Governing Equations",
            "### Separation Design Inputs",
            "### Feed and Internal Flow Derivation",
            "### Hydraulics Basis",
            "### Reboiler and Condenser Package Basis",
            "### Heat-Transfer Package Inputs",
            "### Unit-by-Unit Feed / Product / Recycle Summary",
            "### Key Process-Unit Component Balance",
        ],
        notes="Benchmark report contains a dedicated deep main-column design chapter.",
    ),
    "equipment_design_sizing": ReportChapterContract(
        chapter_id="equipment_design_sizing",
        benchmark_title="Sizing of Equipment",
        required_outputs=["equipment_list"],
        required_markers=[
            "### Storage and Inventory Vessel Basis",
            "### Major Process Equipment Basis",
            "### Heat Exchanger and Thermal-Service Basis",
            "### Rotating and Auxiliary Package Basis",
            "### Utility-Coupled Package Inventory",
            "### Datasheet Coverage Matrix",
            "### Equipment-by-Equipment Sizing Summary",
        ],
        notes="Benchmark report includes an equipment-wide sizing chapter.",
    ),
    "mechanical_design_moc": ReportChapterContract(
        chapter_id="mechanical_design_moc",
        benchmark_title="Mechanical Design and Material of Construction",
        required_outputs=["mechanical_design_moc"],
        required_markers=[
            "### Mechanical Basis",
            "### Mechanical Design Input Matrix",
            "### Shell and Head Thickness Derivation",
            "### Support and Overturning Derivation",
            "### Nozzle Reinforcement and Connection Basis",
            "### Connection and Piping Class Basis",
            "### Material of Construction Matrix",
            "### MoC Option Screening",
            "### Equipment-Wise MoC Justification Matrix",
            "### Inspection and Maintainability Basis",
            "### Corrosion and Service Basis",
            "### Utility and Storage MoC Basis",
        ],
        notes="Benchmark report separates mechanical design and MoC into dedicated sections.",
    ),
    "storage_utilities": ReportChapterContract(
        chapter_id="storage_utilities",
        benchmark_title="Storage & Utilities",
        required_outputs=["utility_summary"],
        required_markers=[
            "### Storage Inventory and Buffer Basis",
            "### Storage Service Matrix",
            "### Utility Consumption Summary",
            "### Utility Service System Matrix",
            "### Utility Peak and Annualized Demand",
            "### Utility Demand by Major Unit",
            "### Utility Island Service Basis",
            "### Header and Thermal-Loop Basis",
        ],
        notes="Benchmark report includes dedicated storage and utility architecture coverage.",
    ),
    "instrumentation_control": ReportChapterContract(
        chapter_id="instrumentation_control",
        benchmark_title="Instrumentation & Process Control",
        required_outputs=["control_plan"],
        required_markers=[
            "### Control Philosophy",
            "### Loop Objective Matrix",
            "### Controlled and Manipulated Variable Register",
            "### Startup, Shutdown, and Override Basis",
            "### Alarm and Interlock Basis",
            "### Utility-Integrated Control Basis",
            "### Control Loop Sheets",
        ],
        notes="Benchmark report includes a dedicated control philosophy chapter.",
    ),
    "hazop": ReportChapterContract(
        chapter_id="hazop",
        benchmark_title="HAZOP",
        required_outputs=["hazop_study", "hazop_node_register"],
        required_markers=[
            "### HAZOP Coverage Summary",
            "### HAZOP Node Basis",
            "### Critical Node Summary",
            "### Deviation Cause-Consequence Matrix",
            "### Recommendation Register",
        ],
        notes="Benchmark report includes node-based HAZOP tables.",
    ),
    "safety_health_environment_waste": ReportChapterContract(
        chapter_id="safety_health_environment_waste",
        benchmark_title="Safety, Health & Environment",
        required_outputs=["safety_environment"],
        required_markers=[
            "### Safety Basis",
            "### Hazard and Emergency Response Basis",
            "### Health and Exposure Basis",
            "### Environmental and Waste Basis",
            "### Environmental Control and Monitoring Basis",
            "### Waste Handling and Disposal Basis",
            "### Safeguard Linkage",
        ],
        notes="Benchmark report includes a dedicated SHE chapter.",
    ),
    "layout": ReportChapterContract(
        chapter_id="layout",
        benchmark_title="Project & Plant Layout",
        required_outputs=["layout"],
        required_markers=[
            "### Plot Plan Basis",
            "### Plot Layout Schematic",
            "### Area Zoning and Separation Basis",
            "### Equipment Placement Matrix",
            "### Utility Corridor Matrix",
            "### Utility Routing and Access Basis",
            "### Dispatch and Emergency Access Basis",
        ],
        notes="Benchmark report includes plant layout figures and notes.",
    ),
    "project_cost": ReportChapterContract(
        chapter_id="project_cost",
        benchmark_title="Project Cost",
        required_outputs=["cost_model", "plant_cost_summary", "procurement_basis_decision", "logistics_basis_decision"],
        required_markers=[
            "### Procurement Basis",
            "### Logistics Basis",
            "### Project Cost Build-Up Summary",
            "### Direct Plant Cost Head Allocation",
            "### Indirect and Contingency Basis",
            "### Equipment Family Cost Allocation",
            "### Procurement Timing Basis",
            "### Installed Equipment Cost Matrix",
        ],
        notes="Benchmark report includes project-cost buildup tables.",
    ),
    "cost_of_production": ReportChapterContract(
        chapter_id="cost_of_production",
        benchmark_title="Cost of Production",
        required_outputs=["cost_model"],
        required_markers=[
            "### Cost of Production Summary",
            "### Manufacturing Cost Build-Up",
            "### Utility and Raw-Material Cost Basis",
            "### Unit Cost and Selling Basis",
        ],
        notes="Benchmark report includes cost-of-production breakdown tables.",
    ),
    "working_capital": ReportChapterContract(
        chapter_id="working_capital",
        benchmark_title="Working Capital",
        required_outputs=["working_capital_model"],
        required_markers=[
            "### Working-Capital Parameter Basis",
            "### Working-Capital Breakdown",
            "### Inventory, Receivable, and Payable Basis",
            "### Procurement-Linked Working-Capital Timing",
            "### Operations Planning Basis",
        ],
        notes="Benchmark report includes a dedicated working-capital chapter.",
    ),
    "financial_analysis": ReportChapterContract(
        chapter_id="financial_analysis",
        benchmark_title="Financial Analysis",
        required_outputs=["financial_model", "economic_basis_decision", "financing_basis_decision", "debt_schedule", "tax_depreciation_basis", "financial_schedule"],
        required_markers=[
            "### Financing Basis",
            "### Financial Performance Summary",
            "### Profitability and Return Summary",
            "### Funding and Capital Structure Basis",
            "### Procurement-Linked Working-Capital Basis",
            "### Debt Service Coverage Schedule",
            "### Profit and Loss Schedule",
            "### Cash Accrual and Funding Schedule",
            "### Lender Coverage Screening",
        ],
        notes="Benchmark report includes multi-year finance schedules and returns.",
    ),
    "conclusion": ReportChapterContract(
        chapter_id="conclusion",
        benchmark_title="Conclusion",
        notes="Benchmark report includes a standalone conclusion chapter.",
    ),
}

_SUPPORT_CONTRACTS: list[ReportSupportContract] = [
    ReportSupportContract(
        support_id="references",
        benchmark_title="References",
        required_markers=["## References"],
        notes="Benchmark report includes a dedicated references chapter.",
    ),
    ReportSupportContract(
        support_id="appendix_msds",
        benchmark_title="Appendix A: Material Safety Data Sheet",
        required_markers=["Material Safety Data Sheet"],
        notes="Benchmark report contains an MSDS appendix.",
    ),
    ReportSupportContract(
        support_id="appendix_code_backup",
        benchmark_title="Appendix B: Python Code",
        required_markers=["Python Code"],
        notes="Benchmark report contains a code appendix.",
    ),
    ReportSupportContract(
        support_id="appendix_process_design_datasheets",
        benchmark_title="Appendix C: Process Design Data Sheet",
        required_markers=["Process Design Data Sheet"],
        notes="Benchmark report contains a process design datasheet appendix.",
    ),
]


def _contract_markdown(chapter_contracts: list[ReportChapterContract], support_contracts: list[ReportSupportContract]) -> str:
    lines = [
        "## Report Parity Framework",
        "",
        "### Chapter Contract",
        "",
        "| Chapter ID | Benchmark Title | Required Outputs | Required Markers | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for contract in chapter_contracts:
        lines.append(
            "| "
            + " | ".join(
                [
                    contract.chapter_id,
                    contract.benchmark_title,
                    ", ".join(contract.required_outputs) or "-",
                    ", ".join(contract.required_markers) or "-",
                    contract.notes or "-",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "### Support Contract",
            "",
            "| Support ID | Benchmark Title | Required Markers | Notes |",
            "| --- | --- | --- | --- |",
        ]
    )
    for contract in support_contracts:
        lines.append(
            "| "
            + " | ".join(
                [
                    contract.support_id,
                    contract.benchmark_title,
                    ", ".join(contract.required_markers) or "-",
                    contract.notes or "-",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def build_report_parity_framework(benchmark_manifest: BenchmarkManifest) -> ReportParityFrameworkArtifact:
    chapter_contracts = [_CHAPTER_LIBRARY[chapter_id] for chapter_id in benchmark_manifest.required_chapters if chapter_id in _CHAPTER_LIBRARY]
    support_contracts = list(_SUPPORT_CONTRACTS)
    return ReportParityFrameworkArtifact(
        framework_id=f"{benchmark_manifest.benchmark_id}_report_parity_framework",
        benchmark_id=benchmark_manifest.benchmark_id,
        chapter_contracts=chapter_contracts,
        support_contracts=support_contracts,
        markdown=_contract_markdown(chapter_contracts, support_contracts),
    )


def _result_status(present: bool, missing_outputs: list[str], missing_markers: list[str], citation_count: int, requires_citations: bool) -> ReportParityStatus:
    if not present:
        return ReportParityStatus.MISSING
    if missing_outputs or missing_markers or (requires_citations and citation_count == 0):
        return ReportParityStatus.PARTIAL
    return ReportParityStatus.COMPLETE


def evaluate_report_parity(
    framework: ReportParityFrameworkArtifact,
    chapters: list[ChapterArtifact],
    references_md: str,
    annexures_md: str,
) -> ReportParityArtifact:
    chapter_map = {chapter.chapter_id: chapter for chapter in chapters}
    chapter_results: list[ChapterParityResult] = []
    missing_chapter_ids: list[str] = []

    for contract in framework.chapter_contracts:
        chapter = chapter_map.get(contract.chapter_id)
        if chapter is None:
            chapter_results.append(
                ChapterParityResult(
                    chapter_id=contract.chapter_id,
                    benchmark_title=contract.benchmark_title,
                    status=ReportParityStatus.MISSING,
                    present=False,
                    notes=[contract.notes] if contract.notes else [],
                )
            )
            missing_chapter_ids.append(contract.chapter_id)
            continue
        lowered_markdown = chapter.rendered_markdown.lower()
        missing_outputs = [output_id for output_id in contract.required_outputs if output_id not in chapter.produced_outputs]
        missing_markers = [marker for marker in contract.required_markers if marker.lower() not in lowered_markdown]
        citation_count = len(chapter.citations)
        notes = [contract.notes] if contract.notes else []
        if contract.requires_citations and citation_count == 0:
            notes.append("Missing citations for a benchmark-required chapter.")
        status = _result_status(bool(chapter), missing_outputs, missing_markers, citation_count, contract.requires_citations)
        chapter_results.append(
            ChapterParityResult(
                chapter_id=contract.chapter_id,
                benchmark_title=contract.benchmark_title,
                status=status,
                present=True,
                citation_count=citation_count,
                missing_outputs=missing_outputs,
                missing_markers=missing_markers,
                notes=notes,
            )
        )
        if status == ReportParityStatus.MISSING:
            missing_chapter_ids.append(contract.chapter_id)

    support_text = {
        "references": references_md,
        "appendix_msds": annexures_md,
        "appendix_code_backup": annexures_md,
        "appendix_process_design_datasheets": annexures_md,
    }
    support_results: list[SupportParityResult] = []
    missing_support_ids: list[str] = []
    for contract in framework.support_contracts:
        text = support_text.get(contract.support_id, "")
        present = bool(text.strip())
        lowered_text = text.lower()
        missing_markers = [marker for marker in contract.required_markers if marker.lower() not in lowered_text]
        status = ReportParityStatus.MISSING if (not present or missing_markers) else ReportParityStatus.COMPLETE
        support_results.append(
            SupportParityResult(
                support_id=contract.support_id,
                benchmark_title=contract.benchmark_title,
                status=status,
                present=present,
                missing_markers=missing_markers,
                notes=[contract.notes] if contract.notes else [],
            )
        )
        if status == ReportParityStatus.MISSING:
            missing_support_ids.append(contract.support_id)

    complete_chapter_count = sum(1 for result in chapter_results if result.status == ReportParityStatus.COMPLETE)
    partial_chapter_count = sum(1 for result in chapter_results if result.status == ReportParityStatus.PARTIAL)
    missing_chapter_count = sum(1 for result in chapter_results if result.status == ReportParityStatus.MISSING)
    complete_support_count = sum(1 for result in support_results if result.status == ReportParityStatus.COMPLETE)
    partial_support_count = sum(1 for result in support_results if result.status == ReportParityStatus.PARTIAL)
    missing_support_count = sum(1 for result in support_results if result.status == ReportParityStatus.MISSING)
    overall_status = (
        ReportParityStatus.COMPLETE
        if missing_chapter_count == 0 and missing_support_count == 0 and partial_chapter_count == 0 and partial_support_count == 0
        else ReportParityStatus.PARTIAL
    )

    lines = [
        "## Report Parity Assessment",
        "",
        f"- Benchmark profile: `{framework.benchmark_id}`",
        f"- Overall status: `{overall_status.value}`",
        f"- Chapters complete / partial / missing: `{complete_chapter_count}/{partial_chapter_count}/{missing_chapter_count}`",
        f"- Support sections complete / partial / missing: `{complete_support_count}/{partial_support_count}/{missing_support_count}`",
        "",
        "### Missing Chapter IDs",
        "",
        ", ".join(missing_chapter_ids) if missing_chapter_ids else "None.",
        "",
        "### Missing Support IDs",
        "",
        ", ".join(missing_support_ids) if missing_support_ids else "None.",
        "",
        "### Chapter Status Table",
        "",
        "| Chapter ID | Benchmark Title | Status | Missing Outputs | Missing Markers |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in chapter_results:
        lines.append(
            "| "
            + " | ".join(
                [
                    result.chapter_id,
                    result.benchmark_title,
                    result.status.value,
                    ", ".join(result.missing_outputs) or "-",
                    ", ".join(result.missing_markers) or "-",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "### Support Section Status Table",
            "",
            "| Support ID | Benchmark Title | Status | Missing Markers |",
            "| --- | --- | --- | --- |",
        ]
    )
    for result in support_results:
        lines.append(
            "| "
            + " | ".join(
                [
                    result.support_id,
                    result.benchmark_title,
                    result.status.value,
                    ", ".join(result.missing_markers) or "-",
                ]
            )
            + " |"
        )

    return ReportParityArtifact(
        framework_id=framework.framework_id,
        benchmark_id=framework.benchmark_id,
        overall_status=overall_status,
        complete_chapter_count=complete_chapter_count,
        partial_chapter_count=partial_chapter_count,
        missing_chapter_count=missing_chapter_count,
        complete_support_count=complete_support_count,
        partial_support_count=partial_support_count,
        missing_support_count=missing_support_count,
        missing_chapter_ids=missing_chapter_ids,
        missing_support_ids=missing_support_ids,
        chapter_results=chapter_results,
        support_results=support_results,
        markdown="\n".join(lines),
    )


def evaluate_report_acceptance(
    benchmark_manifest: BenchmarkManifest,
    report_parity: ReportParityArtifact | None,
    decision_presence: dict[str, bool],
    pipeline_status: RunStatus,
    blocked_stage_id: str | None = None,
    blocking_issues: list[ValidationIssue] | None = None,
) -> ReportAcceptanceArtifact:
    blocking_issues = blocking_issues or []
    decision_results = [
        DecisionAcceptanceResult(
            decision_id=decision_id,
            present=decision_presence.get(decision_id, False),
            notes=[] if decision_presence.get(decision_id, False) else ["Expected benchmark decision not yet resolved."],
        )
        for decision_id in benchmark_manifest.expected_decisions
    ]
    missing_expected_decisions = [result.decision_id for result in decision_results if not result.present]
    conditional_notes: list[str] = []
    report_parity_status = report_parity.overall_status if report_parity else None
    if report_parity is None:
        conditional_notes.append("Report parity has not been evaluated for this run state yet.")
    elif report_parity.overall_status != ReportParityStatus.COMPLETE:
        conditional_notes.append(
            "Report parity remains incomplete: "
            f"{report_parity.partial_chapter_count} partial chapters, "
            f"{report_parity.partial_support_count} partial support sections, "
            f"{report_parity.missing_support_count} missing support sections."
        )
    if missing_expected_decisions:
        conditional_notes.append("Expected benchmark decisions still missing: " + ", ".join(missing_expected_decisions) + ".")

    if pipeline_status == RunStatus.BLOCKED:
        overall_status = ReportAcceptanceStatus.BLOCKED
        summary = (
            f"Benchmark '{benchmark_manifest.benchmark_id}' is honestly blocked at stage "
            f"'{blocked_stage_id or 'unknown'}' with {len(blocking_issues)} blocking issues."
        )
    elif report_parity is not None and report_parity.overall_status == ReportParityStatus.COMPLETE and not missing_expected_decisions:
        overall_status = ReportAcceptanceStatus.COMPLETE
        summary = f"Benchmark '{benchmark_manifest.benchmark_id}' meets the current report-parity and expected-decision acceptance gate."
    else:
        overall_status = ReportAcceptanceStatus.CONDITIONAL
        summary = (
            f"Benchmark '{benchmark_manifest.benchmark_id}' completed without a hard block, "
            "but the acceptance gate remains conditional."
        )

    lines = [
        "## Final Acceptance Gate",
        "",
        f"- Benchmark profile: `{benchmark_manifest.benchmark_id}`",
        f"- Pipeline status at evaluation: `{pipeline_status.value}`",
        f"- Acceptance status: `{overall_status.value}`",
        f"- Report parity status: `{report_parity_status.value if report_parity_status else 'not_evaluated'}`",
        f"- Blocked stage: `{blocked_stage_id or 'none'}`",
        f"- Expected decisions satisfied / missing: `{sum(1 for item in decision_results if item.present)}/{len(missing_expected_decisions)}`",
        f"- Blocking issue codes: `{', '.join(issue.code for issue in blocking_issues) or 'none'}`",
        "",
        "### Acceptance Summary",
        "",
        summary,
        "",
        "### Conditional Notes",
        "",
        "\n".join(f"- {note}" for note in conditional_notes) if conditional_notes else "None.",
        "",
        "### Expected Decision Coverage",
        "",
        "| Decision | Present | Notes |",
        "| --- | --- | --- |",
    ]
    for result in decision_results:
        lines.append(
            "| "
            + " | ".join(
                [
                    result.decision_id,
                    "yes" if result.present else "no",
                    "; ".join(result.notes) or "-",
                ]
            )
            + " |"
        )

    return ReportAcceptanceArtifact(
        benchmark_id=benchmark_manifest.benchmark_id,
        overall_status=overall_status,
        pipeline_status=pipeline_status,
        report_parity_status=report_parity_status,
        blocked_stage_id=blocked_stage_id,
        satisfied_expected_decision_count=sum(1 for item in decision_results if item.present),
        missing_expected_decision_count=len(missing_expected_decisions),
        missing_expected_decisions=missing_expected_decisions,
        blocking_issue_codes=[issue.code for issue in blocking_issues],
        decision_results=decision_results,
        conditional_notes=conditional_notes,
        summary=summary,
        markdown="\n".join(lines),
    )
