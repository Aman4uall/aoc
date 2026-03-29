from __future__ import annotations

from aoc.models import (
    AgentDecisionFabricArtifact,
    AlternativeOption,
    CriticFinding,
    CriticRegistryArtifact,
    CriticVerdict,
    DecisionPacket,
    DecisionRecord,
    OptionSet,
    PropertyEstimate,
    ResolvedSourceSet,
    ResolvedValueArtifact,
    SourceCandidateSet,
)


ROLE_MAP = {
    "capacity_case": "SourceScout",
    "site_selection": "SourceScout",
    "route_selection": "RouteSynthesizer",
    "reactor_choice": "UnitDesignEngineer",
    "separation_choice": "UnitDesignEngineer",
    "exchanger_choice": "UtilityIntegrator",
    "storage_choice": "UnitDesignEngineer",
    "moc_choice": "MechanicalDesigner",
    "utility_basis": "UtilityIntegrator",
    "economic_basis": "CostEngineer",
    "procurement_basis": "CostEngineer",
    "logistics_basis": "CostEngineer",
    "financing_basis": "CostEngineer",
    "thermo_method": "PropertyResolver",
    "kinetics_method": "PropertyResolver",
    "control_architecture": "Critic",
    "layout_choice": "Critic",
}


def _status_for_decision(decision: DecisionRecord) -> tuple[str, str, list[str], str]:
    if not decision.selected_candidate_id:
        return (
            "blocked",
            f"Decision '{decision.decision_id}' has no selected candidate.",
            ["decision_missing_selection"],
            "Review the generated alternatives and force a deterministic selection.",
        )
    selected = next((item for item in decision.alternatives if item.candidate_id == decision.selected_candidate_id), None)
    if selected is None or not selected.feasible:
        return (
            "blocked",
            f"Decision '{decision.decision_id}' selected an infeasible or missing candidate.",
            ["decision_selected_candidate_infeasible"],
            "Re-run the option scoring after removing infeasible candidates.",
        )
    if decision.approval_required or decision.blocked_value_ids:
        return (
            "warning",
            f"Decision '{decision.decision_id}' is usable but still requires analyst review.",
            ["approval_required"] + (["blocked_values_present"] if decision.blocked_value_ids else []),
            "Approve the decision or improve the evidence basis to clear the warning.",
        )
    return (
        "pass",
        f"Decision '{decision.decision_id}' passed deterministic scoring and critic review.",
        [],
        "No further action required.",
    )


def _packet_from_decision(decision: DecisionRecord) -> DecisionPacket:
    specialist_role = ROLE_MAP.get(decision.decision_id, "Critic")
    option_set = OptionSet(
        option_set_id=f"{decision.decision_id}_options",
        specialist_role=specialist_role,
        context=decision.context,
        alternatives=decision.alternatives,
        selected_candidate_id=decision.selected_candidate_id,
        markdown="\n".join(
            [
                f"Selected candidate: {decision.selected_candidate_id or 'n/a'}",
                f"Confidence: {decision.confidence:.2f}",
                f"Scenario stability: {decision.scenario_stability.value}",
            ]
        ),
        citations=decision.citations,
        assumptions=decision.assumptions,
    )
    status, message, issue_codes, recommended_action = _status_for_decision(decision)
    verdict = CriticVerdict(
        verdict_id=f"{decision.decision_id}_critic",
        specialist_role="Critic",
        status=status,
        decision_id=decision.decision_id,
        message=message,
        blocking_issue_codes=issue_codes,
        recommended_action=recommended_action,
        citations=decision.citations,
        assumptions=decision.assumptions,
    )
    markdown = "\n".join(
        [
            f"### {decision.decision_id}",
            "",
            f"- specialist_role: {specialist_role}",
            f"- selected_candidate: {decision.selected_candidate_id or 'n/a'}",
            f"- critic_status: {status}",
            f"- summary: {decision.selected_summary}",
        ]
    )
    return DecisionPacket(
        packet_id=f"{decision.decision_id}_packet",
        specialist_role=specialist_role,
        context=decision.context,
        option_set=option_set,
        selected_decision=decision,
        critic_verdicts=[verdict],
        markdown=markdown,
        citations=decision.citations,
        assumptions=decision.assumptions,
    )


def _packet_from_source_group(group: SourceCandidateSet) -> DecisionPacket:
    alternatives = [
        AlternativeOption(
            candidate_id=candidate.source_id,
            candidate_type="source_candidate",
            description=f"{group.source_domain.value} source candidate",
            outputs={
                "authority": f"{candidate.authority_score:.1f}",
                "recency": f"{candidate.recency_score:.1f}",
                "geography": f"{candidate.geography_score:.1f}",
                "consistency": f"{candidate.consistency_score:.1f}",
            },
            score_breakdown={"total": candidate.total_score},
            total_score=candidate.total_score,
            feasible=True,
            citations=group.citations,
            assumptions=group.assumptions,
        )
        for candidate in group.candidates
    ]
    selected_id = group.selected_source_ids[0] if group.selected_source_ids else None
    status = "warning" if group.unresolved_conflict else "pass"
    verdict = CriticVerdict(
        verdict_id=f"{group.group_id}_critic",
        specialist_role="Critic",
        status=status,
        decision_id=group.group_id,
        message=(
            f"Source group '{group.group_id}' still has an unresolved conflict."
            if group.unresolved_conflict
            else f"Source group '{group.group_id}' is resolved."
        ),
        blocking_issue_codes=["source_conflict"] if group.unresolved_conflict else [],
        recommended_action="Review the top-ranked sources and confirm the preferred basis." if group.unresolved_conflict else "No action required.",
        citations=group.citations,
        assumptions=group.assumptions,
    )
    return DecisionPacket(
        packet_id=f"{group.group_id}_packet",
        specialist_role="SourceScout",
        context=f"Source ranking for {group.source_domain.value}.",
        option_set=OptionSet(
            option_set_id=f"{group.group_id}_options",
            specialist_role="SourceScout",
            context=f"Source ranking for {group.source_domain.value}.",
            alternatives=alternatives,
            selected_candidate_id=selected_id,
            markdown=group.markdown,
            citations=group.citations,
            assumptions=group.assumptions,
        ),
        critic_verdicts=[verdict],
        markdown=f"Selected source(s): {', '.join(group.selected_source_ids) or 'none'}",
        citations=group.citations,
        assumptions=group.assumptions,
    )


def _packet_from_property_estimate(estimate: PropertyEstimate) -> DecisionPacket:
    alternatives = [
        AlternativeOption(
            candidate_id=method.value,
            candidate_type="property_method",
            description=f"{estimate.property_name} via {method.value}",
            total_score=100.0 if method == estimate.selected_method else 70.0 if method.value in {"sourced", "calculated"} else 45.0,
            feasible=not estimate.blocking or method == estimate.selected_method,
            citations=estimate.citations,
            assumptions=estimate.assumptions,
        )
        for method in estimate.candidate_methods
    ]
    status = "blocked" if estimate.blocking else "warning" if estimate.selected_method.value in {"estimated", "analogy"} else "pass"
    verdict = CriticVerdict(
        verdict_id=f"{estimate.estimate_id}_critic",
        specialist_role="Critic",
        status=status,
        decision_id=estimate.estimate_id,
        message=f"Property estimate for '{estimate.property_name}' is using '{estimate.selected_method.value}'.",
        blocking_issue_codes=["high_sensitivity_property_estimate"] if estimate.blocking else [],
        recommended_action="Replace with a stronger sourced basis before downstream design." if estimate.blocking else "Track the estimate in downstream sensitivities.",
        citations=estimate.citations,
        assumptions=estimate.assumptions,
    )
    return DecisionPacket(
        packet_id=f"{estimate.estimate_id}_packet",
        specialist_role="PropertyResolver",
        context=f"Property-estimation packet for {estimate.property_name}.",
        option_set=OptionSet(
            option_set_id=f"{estimate.estimate_id}_options",
            specialist_role="PropertyResolver",
            context=f"Property-estimation packet for {estimate.property_name}.",
            alternatives=alternatives,
            selected_candidate_id=estimate.selected_method.value,
            markdown=estimate.rationale,
            citations=estimate.citations,
            assumptions=estimate.assumptions,
        ),
        critic_verdicts=[verdict],
        markdown=f"Selected property basis: {estimate.selected_method.value}",
        citations=estimate.citations,
        assumptions=estimate.assumptions,
    )


def _packet_from_critic_finding(finding: CriticFinding) -> DecisionPacket:
    verdict = CriticVerdict(
        verdict_id=f"{finding.finding_id}_verdict",
        specialist_role="Critic",
        status="blocked" if finding.severity.value == "blocked" else "warning",
        decision_id=finding.code,
        message=finding.message,
        blocking_issue_codes=finding.source_issue_codes or [finding.code],
        recommended_action=finding.recommended_action,
        citations=finding.citations,
        assumptions=finding.assumptions,
    )
    return DecisionPacket(
        packet_id=f"{finding.finding_id}_packet",
        specialist_role="Critic",
        context=f"{finding.critic_family} critic for stage {finding.stage_id}",
        option_set=OptionSet(
            option_set_id=f"{finding.finding_id}_options",
            specialist_role="Critic",
            context=f"{finding.critic_family} critic for stage {finding.stage_id}",
            alternatives=[],
            selected_candidate_id=None,
            markdown=finding.message,
            citations=finding.citations,
            assumptions=finding.assumptions,
        ),
        critic_verdicts=[verdict],
        markdown=f"{finding.code}: {finding.message}",
        citations=finding.citations,
        assumptions=finding.assumptions,
    )


def build_agent_decision_fabric(
    resolved_sources: ResolvedSourceSet | None,
    resolved_values: ResolvedValueArtifact | None,
    decisions: list[DecisionRecord],
    critic_registry: CriticRegistryArtifact | None = None,
) -> AgentDecisionFabricArtifact:
    packets: list[DecisionPacket] = []
    if resolved_sources:
        packets.extend(_packet_from_source_group(group) for group in resolved_sources.groups)
    if resolved_values:
        packets.extend(_packet_from_property_estimate(estimate) for estimate in resolved_values.property_estimates)
    packets.extend(_packet_from_decision(decision) for decision in decisions)
    if critic_registry:
        packets.extend(_packet_from_critic_finding(finding) for finding in critic_registry.findings)
    rows = [
        "| Packet | Specialist | Selected | Critic Status |",
        "| --- | --- | --- | --- |",
    ]
    for packet in packets:
        selected = packet.option_set.selected_candidate_id or (packet.selected_decision.selected_candidate_id if packet.selected_decision else "n/a")
        critic_status = packet.critic_verdicts[0].status if packet.critic_verdicts else "n/a"
        rows.append(f"| {packet.packet_id} | {packet.specialist_role} | {selected or 'n/a'} | {critic_status} |")
    return AgentDecisionFabricArtifact(
        packets=packets,
        markdown="\n".join(rows),
        citations=sorted({citation for packet in packets for citation in packet.citations}),
        assumptions=sorted({assumption for packet in packets for assumption in packet.assumptions}),
    )
