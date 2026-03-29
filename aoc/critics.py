from __future__ import annotations

from aoc.models import CriticFinding, CriticRegistryArtifact, Severity, SolveResult, ValidationIssue


def _critic_family(issue: ValidationIssue) -> str:
    code = issue.code.lower()
    artifact = (issue.artifact_ref or "").lower()
    if any(token in code for token in ("source", "evidence", "citation", "resolved")):
        return "evidence"
    if any(token in code for token in ("property", "thermo", "henry", "solubility", "binary_interaction", "vle")):
        return "thermo_property"
    if any(token in code for token in ("kinetic", "reaction_extent", "byproduct")):
        return "kinetics_reaction"
    if any(token in code for token in ("separation", "absorber", "column", "distillation", "dryer", "crystallizer", "classifier")):
        return "separation_design"
    if any(token in code for token in ("reactor", "equipment", "moc", "mechanical")):
        return "unit_applicability"
    if any(token in code for token in ("finance", "financial", "cost", "working_capital", "utility", "economic", "covenant")):
        return "economics_finance"
    if any(token in code for token in ("cross", "mismatch", "scenario", "route")) or any(token in artifact for token in ("financial_model", "cost_model", "route_selection")):
        return "cross_chapter"
    return "general"


def _recommended_action(issue: ValidationIssue) -> str:
    code = issue.code.lower()
    if "citation" in code or "source" in code or "evidence" in code:
        return "Strengthen the cited evidence basis before proceeding."
    if any(token in code for token in ("henry", "solubility", "binary_interaction", "thermo", "property")):
        return "Resolve the missing thermodynamic/property basis or explicitly downgrade the design claim."
    if "kinetic" in code or "reaction" in code:
        return "Upgrade the kinetics/reaction basis or treat the route as lower-confidence."
    if any(token in code for token in ("absorber", "column", "separation", "dryer", "crystallizer")):
        return "Recheck the selected separation family and design basis against the solved process."
    if any(token in code for token in ("reactor", "equipment", "moc", "mechanical")):
        return "Re-rank the unit family or revise the equipment basis to match the route family."
    if any(token in code for token in ("finance", "financial", "cost", "working_capital", "utility", "economic", "covenant")):
        return "Align the economic and financing basis with the technical architecture and scenarios."
    if "mismatch" in code or "cross" in code:
        return "Resolve the contradiction before the report is treated as internally consistent."
    return "Review the critic finding and either improve the basis or require analyst approval."


def _finding_from_issue(stage_id: str, issue: ValidationIssue) -> CriticFinding:
    return CriticFinding(
        finding_id=f"{stage_id}:{issue.code}:{issue.artifact_ref or 'n/a'}",
        stage_id=stage_id,
        critic_family=_critic_family(issue),
        severity=issue.severity,
        code=issue.code,
        message=issue.message,
        artifact_ref=issue.artifact_ref,
        recommended_action=_recommended_action(issue),
        source_issue_codes=[issue.code],
    )


def _solver_findings(stage_id: str, solve_result: SolveResult | None) -> list[CriticFinding]:
    if solve_result is None:
        return []
    findings: list[CriticFinding] = []
    for index, message in enumerate(solve_result.critic_messages):
        findings.append(
            CriticFinding(
                finding_id=f"{stage_id}:solve_result:{index}",
                stage_id=stage_id,
                critic_family="flowsheet_solver",
                severity=Severity.WARNING,
                code="solve_result_critic_message",
                message=message,
                artifact_ref="solve_result",
                recommended_action="Review the solved flowsheet packets and close the critic message before treating the design as robust.",
                source_issue_codes=["solve_result_critic_message"],
                citations=solve_result.citations,
                assumptions=solve_result.assumptions,
            )
        )
    return findings


def merge_critic_registry(
    existing: CriticRegistryArtifact | None,
    stage_id: str,
    issues: list[ValidationIssue],
    solve_result: SolveResult | None = None,
) -> CriticRegistryArtifact:
    findings = {finding.finding_id: finding for finding in (existing.findings if existing else [])}
    for issue in issues:
        finding = _finding_from_issue(stage_id, issue)
        findings[finding.finding_id] = finding
    for finding in _solver_findings(stage_id, solve_result):
        findings[finding.finding_id] = finding
    ordered = sorted(findings.values(), key=lambda item: (item.stage_id, item.severity.value, item.code, item.finding_id))
    warning_count = sum(1 for item in ordered if item.severity == Severity.WARNING)
    blocked_count = sum(1 for item in ordered if item.severity == Severity.BLOCKED)
    rows = [
        "| Stage | Family | Severity | Code | Artifact | Message |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for finding in ordered:
        rows.append(
            f"| {finding.stage_id} | {finding.critic_family} | {finding.severity.value} | {finding.code} | {finding.artifact_ref or '-'} | {finding.message} |"
        )
    return CriticRegistryArtifact(
        findings=ordered,
        warning_count=warning_count,
        blocked_count=blocked_count,
        markdown="\n".join(rows),
        citations=sorted({citation for finding in ordered for citation in finding.citations}),
        assumptions=sorted({assumption for finding in ordered for assumption in finding.assumptions}),
    )
