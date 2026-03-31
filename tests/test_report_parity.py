import unittest

from aoc.models import BenchmarkManifest, ChapterArtifact, ChapterStatus, ReportAcceptanceStatus, ReportParityStatus, RunStatus, Severity, SourceDomain, ValidationIssue
from aoc.report_parity import build_report_parity_framework, evaluate_report_acceptance, evaluate_report_parity


class ReportParityTests(unittest.TestCase):
    def test_build_report_parity_framework_includes_benchmark_chapters_and_support(self):
        manifest = BenchmarkManifest(
            benchmark_id="ethylene_glycol",
            target_product="Ethylene glycol",
            archetype_family="continuous_liquid_organic_heat_integrated",
            required_chapters=["executive_summary", "material_balance", "financial_analysis"],
            expected_decisions=[],
            required_public_source_domains=[SourceDomain.TECHNICAL],
        )

        framework = build_report_parity_framework(manifest)

        self.assertEqual(framework.benchmark_id, "ethylene_glycol")
        self.assertEqual([item.chapter_id for item in framework.chapter_contracts], ["executive_summary", "material_balance", "financial_analysis"])
        self.assertTrue(any(item.support_id == "references" for item in framework.support_contracts))
        self.assertTrue(any(item.support_id == "appendix_msds" for item in framework.support_contracts))

    def test_evaluate_report_parity_marks_missing_appendices_as_partial_gap(self):
        manifest = BenchmarkManifest(
            benchmark_id="ethylene_glycol",
            target_product="Ethylene glycol",
            archetype_family="continuous_liquid_organic_heat_integrated",
            required_chapters=["executive_summary", "material_balance"],
            expected_decisions=[],
            required_public_source_domains=[SourceDomain.TECHNICAL],
        )
        framework = build_report_parity_framework(manifest)
        chapters = [
            ChapterArtifact(
                chapter_id="executive_summary",
                title="Executive Summary",
                stage_id="final_report",
                status=ChapterStatus.COMPLETE,
                citations=["src-1"],
                rendered_markdown="## Executive Summary\n\nSummary text.",
            ),
            ChapterArtifact(
                chapter_id="material_balance",
                title="Material Balance",
                stage_id="material_balance",
                status=ChapterStatus.COMPLETE,
                citations=["src-1"],
                produced_outputs=["stream_table"],
                rendered_markdown=(
                    "## Material Balance\n\n"
                    "### Overall Plant Balance Summary\n\nTable content.\n\n"
                    "### Section Balance Summary\n\nTable content.\n\n"
                    "### Unit Packet Balance Summary\n\nTable content.\n\n"
                    "### Long Stream Ledger\n\nTable content."
                ),
            ),
        ]

        parity = evaluate_report_parity(
            framework,
            chapters,
            references_md="## References\n\n- **src-1**: reference.",
            annexures_md="## Annexures\n\n### Calculation Traces\n\nAvailable.",
        )

        self.assertEqual(parity.overall_status, ReportParityStatus.PARTIAL)
        self.assertEqual(parity.missing_chapter_ids, [])
        self.assertIn("appendix_msds", parity.missing_support_ids)
        self.assertIn("appendix_code_backup", parity.missing_support_ids)
        self.assertEqual(
            next(item for item in parity.chapter_results if item.chapter_id == "material_balance").status,
            ReportParityStatus.COMPLETE,
        )

    def test_evaluate_report_acceptance_marks_complete_when_parity_and_decisions_close(self):
        manifest = BenchmarkManifest(
            benchmark_id="ethylene_glycol",
            target_product="Ethylene glycol",
            archetype_family="continuous_liquid_organic_heat_integrated",
            required_chapters=["executive_summary"],
            expected_decisions=["capacity_case", "route_selection"],
            required_public_source_domains=[SourceDomain.TECHNICAL],
        )
        framework = build_report_parity_framework(manifest)
        parity = evaluate_report_parity(
            framework,
            [
                ChapterArtifact(
                    chapter_id="executive_summary",
                    title="Executive Summary",
                    stage_id="final_report",
                    status=ChapterStatus.COMPLETE,
                    citations=["src-1"],
                    rendered_markdown="## Executive Summary\n\nSummary text.",
                )
            ],
            references_md="## References\n\n- **src-1**: reference.",
            annexures_md=(
                "## Annexures\n\n"
                "### Appendix A: Material Safety Data Sheet\n\nAvailable.\n\n"
                "### Appendix B: Python Code and Reproducibility Bundle\n\nAvailable.\n\n"
                "### Appendix C: Process Design Data Sheet\n\nAvailable."
            ),
        )
        acceptance = evaluate_report_acceptance(
            manifest,
            parity,
            {"capacity_case": True, "route_selection": True},
            RunStatus.AWAITING_APPROVAL,
        )
        self.assertEqual(acceptance.overall_status, ReportAcceptanceStatus.COMPLETE)
        self.assertEqual(acceptance.missing_expected_decision_count, 0)

    def test_evaluate_report_acceptance_marks_blocked_for_honest_sparse_data_stop(self):
        manifest = BenchmarkManifest(
            benchmark_id="para_nitroanisole",
            target_product="para-Nitroanisole",
            archetype_family="specialty_aromatic_separation_intensive",
            required_chapters=["executive_summary"],
            expected_decisions=["capacity_case", "route_selection"],
            required_public_source_domains=[SourceDomain.TECHNICAL],
        )
        acceptance = evaluate_report_acceptance(
            manifest,
            report_parity=None,
            decision_presence={"capacity_case": True, "route_selection": False},
            pipeline_status=RunStatus.BLOCKED,
            blocked_stage_id="property_gap_resolution",
            blocking_issues=[
                ValidationIssue(
                    code="missing_property_basis",
                    severity=Severity.BLOCKED,
                    message="Property basis unresolved.",
                    artifact_ref="property_gap",
                )
            ],
        )
        self.assertEqual(acceptance.overall_status, ReportAcceptanceStatus.BLOCKED)
        self.assertEqual(acceptance.blocked_stage_id, "property_gap_resolution")
        self.assertIn("missing_property_basis", acceptance.blocking_issue_codes)


if __name__ == "__main__":
    unittest.main()
