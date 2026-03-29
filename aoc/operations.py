from __future__ import annotations

from aoc.models import (
    AlternativeOption,
    CalcTrace,
    DecisionCriterion,
    DecisionRecord,
    OperationsPlanningArtifact,
    ProcessArchetype,
    ProjectBasis,
    ScenarioStability,
    SensitivityLevel,
)
from aoc.value_engine import make_value_record


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _service_family(archetype: ProcessArchetype) -> str:
    separation = archetype.dominant_separation_family.lower()
    if archetype.dominant_product_phase == "solid" or "crystall" in separation:
        return "solids_crystallization"
    if "absorption" in separation or archetype.dominant_product_phase == "gas":
        return "gas_liquid_absorption"
    if "distillation" in separation or archetype.dominant_product_phase == "liquid":
        return "continuous_liquid_purification"
    return "mixed_purification"


def _availability_policy_label(service_family: str) -> str:
    return {
        "continuous_liquid_purification": "continuous_liquid_train",
        "gas_liquid_absorption": "gas_liquid_loop_availability",
        "solids_crystallization": "solids_campaign_turnaround",
    }.get(service_family, "generic_feasibility_availability")


def _mode_profile(
    basis: ProjectBasis,
    archetype: ProcessArchetype,
    mode: str,
) -> dict[str, float | str]:
    service_family = _service_family(archetype)
    hazard_factor = {"low": 0.92, "moderate": 1.0, "high": 1.12}.get(archetype.hazard_intensity, 1.0)
    scale_factor = _clamp(basis.capacity_tpa / 50_000.0, 0.25, 4.0)
    if service_family == "solids_crystallization":
        profile = (
            {
                "raw_material_buffer_days": 20.0,
                "finished_goods_buffer_days": 8.0,
                "operating_stock_days": 4.0,
                "restart_buffer_days": 2.0,
                "startup_ramp_days": 3.2,
                "campaign_length_days": 110.0,
                "cleaning_cycle_days": 95.0,
                "cleaning_downtime_days": 2.8,
                "turnaround_buffer_factor": 1.08,
                "restart_loss_fraction": 0.010,
            }
            if mode == "continuous"
            else {
                "raw_material_buffer_days": 18.0,
                "finished_goods_buffer_days": 11.0,
                "operating_stock_days": 2.2,
                "restart_buffer_days": 1.2,
                "startup_ramp_days": 1.6,
                "campaign_length_days": 28.0,
                "cleaning_cycle_days": 28.0,
                "cleaning_downtime_days": 1.3,
                "turnaround_buffer_factor": 1.03,
                "restart_loss_fraction": 0.0045,
            }
        )
    elif service_family == "gas_liquid_absorption":
        profile = (
            {
                "raw_material_buffer_days": 18.0,
                "finished_goods_buffer_days": 5.0,
                "operating_stock_days": 2.0,
                "restart_buffer_days": 0.8,
                "startup_ramp_days": 1.5,
                "campaign_length_days": 180.0,
                "cleaning_cycle_days": 180.0,
                "cleaning_downtime_days": 1.4,
                "turnaround_buffer_factor": 1.04,
                "restart_loss_fraction": 0.0035,
            }
            if mode == "continuous"
            else {
                "raw_material_buffer_days": 16.0,
                "finished_goods_buffer_days": 8.0,
                "operating_stock_days": 1.8,
                "restart_buffer_days": 0.7,
                "startup_ramp_days": 1.0,
                "campaign_length_days": 35.0,
                "cleaning_cycle_days": 35.0,
                "cleaning_downtime_days": 0.9,
                "turnaround_buffer_factor": 1.02,
                "restart_loss_fraction": 0.0025,
            }
        )
    elif service_family == "continuous_liquid_purification":
        profile = (
            {
                "raw_material_buffer_days": 16.0,
                "finished_goods_buffer_days": 7.0,
                "operating_stock_days": 2.5,
                "restart_buffer_days": 1.5,
                "startup_ramp_days": 2.0,
                "campaign_length_days": 170.0,
                "cleaning_cycle_days": 150.0,
                "cleaning_downtime_days": 2.0,
                "turnaround_buffer_factor": 1.05,
                "restart_loss_fraction": 0.0055,
            }
            if mode == "continuous"
            else {
                "raw_material_buffer_days": 14.0,
                "finished_goods_buffer_days": 10.0,
                "operating_stock_days": 2.0,
                "restart_buffer_days": 1.0,
                "startup_ramp_days": 1.1,
                "campaign_length_days": 24.0,
                "cleaning_cycle_days": 24.0,
                "cleaning_downtime_days": 1.1,
                "turnaround_buffer_factor": 1.02,
                "restart_loss_fraction": 0.0035,
            }
        )
    else:
        profile = (
            {
                "raw_material_buffer_days": 17.0,
                "finished_goods_buffer_days": 7.0,
                "operating_stock_days": 2.5,
                "restart_buffer_days": 1.2,
                "startup_ramp_days": 2.0,
                "campaign_length_days": 130.0,
                "cleaning_cycle_days": 120.0,
                "cleaning_downtime_days": 1.8,
                "turnaround_buffer_factor": 1.04,
                "restart_loss_fraction": 0.0045,
            }
            if mode == "continuous"
            else {
                "raw_material_buffer_days": 15.0,
                "finished_goods_buffer_days": 9.0,
                "operating_stock_days": 2.0,
                "restart_buffer_days": 0.9,
                "startup_ramp_days": 1.2,
                "campaign_length_days": 30.0,
                "cleaning_cycle_days": 30.0,
                "cleaning_downtime_days": 1.0,
                "turnaround_buffer_factor": 1.02,
                "restart_loss_fraction": 0.0030,
            }
        )
    profile["restart_loss_fraction"] = float(profile["restart_loss_fraction"]) * hazard_factor
    if mode == "continuous":
        profile["raw_material_buffer_days"] = float(profile["raw_material_buffer_days"]) + max(scale_factor - 1.0, 0.0) * 1.2
        profile["finished_goods_buffer_days"] = float(profile["finished_goods_buffer_days"]) + max(scale_factor - 1.0, 0.0) * 0.8
    else:
        profile["finished_goods_buffer_days"] = float(profile["finished_goods_buffer_days"]) + max(scale_factor - 0.5, 0.0) * 1.4
        profile["campaign_length_days"] = max(float(profile["campaign_length_days"]) - max(scale_factor - 1.0, 0.0) * 2.0, 14.0)
    campaign_length = max(float(profile["campaign_length_days"]), 1.0)
    cleaning_downtime = float(profile["cleaning_downtime_days"])
    startup_ramp_days = float(profile["startup_ramp_days"])
    restart_loss_fraction = float(profile["restart_loss_fraction"])
    profile["throughput_loss_fraction"] = _clamp(
        cleaning_downtime / campaign_length + startup_ramp_days / campaign_length * restart_loss_fraction * 8.0,
        0.005,
        0.20,
    )
    daily_output_kg = basis.capacity_tpa * 1000.0 / max(basis.annual_operating_days, 1.0)
    restart_events_per_year = max(basis.annual_operating_days / max(float(profile["cleaning_cycle_days"]), 1.0), 1.0)
    profile["annual_restart_loss_kg"] = daily_output_kg * startup_ramp_days * restart_loss_fraction * restart_events_per_year
    profile["service_family"] = service_family
    profile["availability_policy_label"] = _availability_policy_label(service_family)
    return profile


def _mode_scores(
    basis: ProjectBasis,
    archetype: ProcessArchetype,
    mode: str,
    profile: dict[str, float | str],
) -> dict[str, float]:
    scale_factor = _clamp(basis.capacity_tpa / 50_000.0, 0.10, 4.0)
    integrated_heat = "integrated" in archetype.heat_management_profile or "recovery" in archetype.heat_management_profile
    throughput_support = (
        _clamp(58.0 + scale_factor * 11.0, 45.0, 98.0)
        if mode == "continuous"
        else _clamp(88.0 - scale_factor * 20.0 + (8.0 if basis.capacity_tpa < 15_000 else 0.0), 10.0, 90.0)
    )
    changeover_burden = (
        _clamp(
            95.0 - float(profile["cleaning_downtime_days"]) * 5.0 - max(365.0 / max(float(profile["campaign_length_days"]), 1.0) - 2.0, 0.0) * 6.0,
            40.0,
            97.0,
        )
        if mode == "continuous"
        else _clamp(
            84.0 - float(profile["cleaning_downtime_days"]) * 9.0 - max(365.0 / max(float(profile["campaign_length_days"]), 1.0) - 8.0, 0.0) * 3.0,
            18.0,
            88.0,
        )
    )
    heat_integration_fit = 96.0 if mode == "continuous" and integrated_heat else 84.0 if mode == "continuous" else 42.0 if integrated_heat else 58.0
    outage_recovery = (
        _clamp(
            93.0 - float(profile["startup_ramp_days"]) * 8.0 - float(profile["restart_loss_fraction"]) * 2200.0 - float(profile["restart_buffer_days"]) * 2.5,
            24.0,
            95.0,
        )
        if mode == "continuous"
        else _clamp(
            85.0 - float(profile["startup_ramp_days"]) * 5.0 - float(profile["restart_loss_fraction"]) * 1800.0 - max(scale_factor - 0.6, 0.0) * 15.0,
            18.0,
            92.0,
        )
    )
    total_buffer_days = float(profile["raw_material_buffer_days"]) * 0.30 + float(profile["finished_goods_buffer_days"]) + float(profile["operating_stock_days"]) + float(profile["restart_buffer_days"])
    inventory_burden = (
        _clamp(92.0 - total_buffer_days * 2.1, 28.0, 95.0)
        if mode == "continuous"
        else _clamp(88.0 - total_buffer_days * 2.6 - max(scale_factor - 0.4, 0.0) * 8.0, 15.0, 88.0)
    )
    return {
        "Throughput support": throughput_support,
        "Changeover burden": changeover_burden,
        "Heat integration fit": heat_integration_fit,
        "Outage recovery burden": outage_recovery,
        "Inventory burden": inventory_burden,
    }


def build_operating_mode_and_operations(
    basis: ProjectBasis,
    archetype: ProcessArchetype,
    citations: list[str],
    assumptions: list[str],
) -> tuple[DecisionRecord, OperationsPlanningArtifact]:
    criteria = [
        DecisionCriterion(name="Throughput support", weight=0.28, justification="Large dedicated plants need a mode that can hold throughput without excessive campaign fragmentation."),
        DecisionCriterion(name="Changeover burden", weight=0.16, justification="Cleaning and campaign turnover directly affect uptime and staffing."),
        DecisionCriterion(name="Heat integration fit", weight=0.22, justification="Steady heat duties usually reward continuous operation, especially in integrated trains."),
        DecisionCriterion(name="Outage recovery burden", weight=0.18, justification="Startup losses and ramp time should be explicit in the operating-mode choice."),
        DecisionCriterion(name="Inventory burden", weight=0.16, justification="Higher buffer and operating-stock requirements should penalize the weaker mode."),
    ]
    allowed_modes = list(archetype.operating_mode_candidates or ["continuous"])
    alternatives: list[AlternativeOption] = []
    profiles: dict[str, dict[str, float | str]] = {}
    for mode in allowed_modes:
        profile = _mode_profile(basis, archetype, mode)
        profiles[mode] = profile
        breakdown = _mode_scores(basis, archetype, mode, profile)
        total_score = sum(criterion.weight * breakdown[criterion.name] for criterion in criteria)
        rejected_reasons: list[str] = []
        if mode == "batch" and basis.capacity_tpa >= 50_000:
            rejected_reasons.append(f"Batch mode carries a strong campaign and inventory penalty at {basis.capacity_tpa:,.0f} TPA.")
        alternatives.append(
            AlternativeOption(
                candidate_id=mode,
                candidate_type="operating_mode",
                description=f"{mode.title()} operation",
                inputs={"service_family": str(profile["service_family"]), "capacity_tpa": f"{basis.capacity_tpa:.0f}"},
                outputs={
                    "campaign_length_days": f"{float(profile['campaign_length_days']):.1f}",
                    "throughput_loss_fraction": f"{float(profile['throughput_loss_fraction']):.4f}",
                    "restart_loss_fraction": f"{float(profile['restart_loss_fraction']):.4f}",
                },
                score_breakdown=breakdown,
                total_score=round(total_score, 3),
                rejected_reasons=rejected_reasons,
                feasible=True,
                citations=citations,
                assumptions=assumptions,
            )
        )
    alternatives.sort(key=lambda item: item.total_score, reverse=True)
    selected = alternatives[0]
    selected_profile = profiles[selected.candidate_id]
    runner_up = alternatives[1].total_score if len(alternatives) > 1 else selected.total_score - 12.0
    score_gap = selected.total_score - runner_up
    stability = ScenarioStability.STABLE if score_gap >= 12.0 else ScenarioStability.BORDERLINE if score_gap >= 5.0 else ScenarioStability.UNSTABLE
    decision = DecisionRecord(
        decision_id="operating_mode",
        context="Plant operating mode",
        criteria=criteria,
        alternatives=alternatives,
        selected_candidate_id=selected.candidate_id,
        selected_summary=(
            f"{selected.candidate_id.title()} operation is selected for the {_service_family(archetype).replace('_', ' ')} "
            f"service because it gives the stronger throughput, outage-recovery, and inventory balance."
        ),
        hard_constraint_results=[
            f"Capacity basis: {basis.capacity_tpa:,.0f} TPA",
            f"Service family: {selected_profile['service_family']}",
            f"Availability policy: {selected_profile['availability_policy_label']}",
        ],
        confidence=round(_clamp(0.70 + score_gap / 60.0, 0.70, 0.96), 3),
        scenario_stability=stability,
        approval_required=stability == ScenarioStability.UNSTABLE,
        citations=citations,
        assumptions=assumptions + ["Operating-mode decision uses operations-planning buffers, restart losses, and campaign burden instead of a fixed throughput-only rule."],
    )
    markdown = "\n".join(
        [
            "### Operations Planning Basis",
            "",
            f"Selected operating mode: **{selected.candidate_id}**",
            "",
            "| Parameter | Value |",
            "| --- | --- |",
            f"| Service family | {selected_profile['service_family']} |",
            f"| Availability policy | {selected_profile['availability_policy_label']} |",
            f"| Raw-material buffer (d) | {float(selected_profile['raw_material_buffer_days']):.1f} |",
            f"| Finished-goods buffer (d) | {float(selected_profile['finished_goods_buffer_days']):.1f} |",
            f"| Operating stock (d) | {float(selected_profile['operating_stock_days']):.1f} |",
            f"| Restart buffer (d) | {float(selected_profile['restart_buffer_days']):.1f} |",
            f"| Startup ramp (d) | {float(selected_profile['startup_ramp_days']):.1f} |",
            f"| Campaign length (d) | {float(selected_profile['campaign_length_days']):.1f} |",
            f"| Cleaning cycle (d) | {float(selected_profile['cleaning_cycle_days']):.1f} |",
            f"| Cleaning downtime (d) | {float(selected_profile['cleaning_downtime_days']):.1f} |",
            f"| Restart loss fraction | {float(selected_profile['restart_loss_fraction']):.4f} |",
            f"| Throughput loss fraction | {float(selected_profile['throughput_loss_fraction']):.4f} |",
            f"| Annual restart loss (kg/y) | {float(selected_profile['annual_restart_loss_kg']):,.1f} |",
        ]
    )
    operations = OperationsPlanningArtifact(
        planning_id="operations_planning",
        service_family=str(selected_profile["service_family"]),
        recommended_operating_mode=selected.candidate_id,
        availability_policy_label=str(selected_profile["availability_policy_label"]),
        raw_material_buffer_days=float(selected_profile["raw_material_buffer_days"]),
        finished_goods_buffer_days=float(selected_profile["finished_goods_buffer_days"]),
        operating_stock_days=float(selected_profile["operating_stock_days"]),
        restart_buffer_days=float(selected_profile["restart_buffer_days"]),
        startup_ramp_days=float(selected_profile["startup_ramp_days"]),
        campaign_length_days=float(selected_profile["campaign_length_days"]),
        cleaning_cycle_days=float(selected_profile["cleaning_cycle_days"]),
        cleaning_downtime_days=float(selected_profile["cleaning_downtime_days"]),
        turnaround_buffer_factor=float(selected_profile["turnaround_buffer_factor"]),
        throughput_loss_fraction=float(selected_profile["throughput_loss_fraction"]),
        restart_loss_fraction=float(selected_profile["restart_loss_fraction"]),
        annual_restart_loss_kg=float(selected_profile["annual_restart_loss_kg"]),
        buffer_basis_note="Operations planning basis combines route-family campaign behavior, startup loss, and dispatch buffering so storage, working capital, and financial timing use the same assumptions.",
        markdown=markdown,
        calc_traces=[
            CalcTrace(
                trace_id="ops_throughput_loss",
                title="Operations throughput-loss basis",
                formula="loss = cleaning downtime / campaign length + startup ramp / campaign length * restart loss fraction * 8",
                substitutions={
                    "cleaning_downtime": f"{float(selected_profile['cleaning_downtime_days']):.3f}",
                    "campaign_length": f"{float(selected_profile['campaign_length_days']):.3f}",
                    "startup_ramp": f"{float(selected_profile['startup_ramp_days']):.3f}",
                    "restart_loss_fraction": f"{float(selected_profile['restart_loss_fraction']):.5f}",
                },
                result=f"{float(selected_profile['throughput_loss_fraction']):.6f}",
                units="-",
                notes="Used to keep availability and working-capital logic aligned with the operating-mode choice.",
            ),
            CalcTrace(
                trace_id="ops_restart_loss",
                title="Annual restart-loss basis",
                formula="annual restart loss = daily output * startup ramp * restart loss fraction * restart events per year",
                substitutions={
                    "daily_output_kg": f"{basis.capacity_tpa * 1000.0 / max(basis.annual_operating_days, 1.0):.3f}",
                    "startup_ramp_days": f"{float(selected_profile['startup_ramp_days']):.3f}",
                    "restart_loss_fraction": f"{float(selected_profile['restart_loss_fraction']):.5f}",
                    "restart_events_per_year": f"{max(basis.annual_operating_days / max(float(selected_profile['cleaning_cycle_days']), 1.0), 1.0):.3f}",
                },
                result=f"{float(selected_profile['annual_restart_loss_kg']):.3f}",
                units="kg/y",
                notes="This restart-loss basis is later valued in working capital and finance timing.",
            ),
        ],
        value_records=[
            make_value_record("ops_raw_material_buffer_days", "Raw-material buffer days", selected_profile["raw_material_buffer_days"], "days", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("ops_finished_goods_buffer_days", "Finished-goods buffer days", selected_profile["finished_goods_buffer_days"], "days", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("ops_operating_stock_days", "Operating stock days", selected_profile["operating_stock_days"], "days", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("ops_restart_loss_fraction", "Restart loss fraction", selected_profile["restart_loss_fraction"], "-", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
            make_value_record("ops_annual_restart_loss", "Annual restart loss", selected_profile["annual_restart_loss_kg"], "kg/y", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.HIGH),
        ],
        citations=citations,
        assumptions=assumptions + ["Operations planning uses deterministic route-family defaults and capacity scaling for pre-feasibility scheduling and inventory logic."],
    )
    return decision, operations
