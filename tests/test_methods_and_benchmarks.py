import shutil
import tempfile
import unittest
from pathlib import Path

from aoc.config import load_project_config
from aoc.methods import build_capacity_decision, build_kinetics_method_decision, build_thermo_method_decision
from aoc.models import ModelSettings, ProjectBasis, ProjectConfig
from aoc.pipeline import PipelineRunner
from aoc.reasoning import build_reasoning_service
from aoc.research import ResearchManager
from aoc.decision_engine import resolve_property_gaps
from aoc.evidence import build_resolved_source_set, build_resolved_value_artifact


class MethodAndBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aoc-benchmarks-")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_method_decisions_are_emitted_for_eg(self):
        config = load_project_config(str(Path("examples/ethylene_glycol_india_mock.yaml").resolve()))
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        market = reasoning.build_market_assessment(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        property_gap = resolve_property_gaps(profile, config)
        resolved_sources = build_resolved_source_set(config, bundle)
        resolved_values = build_resolved_value_artifact(property_gap, resolved_sources, config)
        capacity = build_capacity_decision(config, market)
        thermo = build_thermo_method_decision(config, survey.routes[0], resolved_values)
        kinetics = build_kinetics_method_decision(config, survey.routes[0], resolved_values)
        self.assertTrue(capacity.selected_candidate_id)
        self.assertIn(thermo.decision.selected_candidate_id, {"direct_public_data", "correlation_interpolation"})
        self.assertIn(kinetics.decision.selected_candidate_id, {"cited_rate_law", "arrhenius_fit"})

    def _run_benchmark(self, example_name: str) -> str:
        config = load_project_config(str(Path(example_name).resolve()))
        config.output_root = self.temp_dir
        runner = PipelineRunner(config)
        while True:
            state = runner.run()
            if state.awaiting_gate_id:
                runner.approve_gate(state.awaiting_gate_id, notes="auto-approved in benchmark test")
                continue
            if state.run_status.value == "completed":
                break
            self.assertNotEqual(state.run_status.value, "blocked", msg=runner.inspect())
        return runner.inspect()

    def _run_expected_block(self, example_name: str) -> tuple[object, str]:
        config = load_project_config(str(Path(example_name).resolve()))
        config.output_root = self.temp_dir
        runner = PipelineRunner(config)
        while True:
            state = runner.run()
            if state.awaiting_gate_id:
                runner.approve_gate(state.awaiting_gate_id, notes="auto-approved in benchmark test")
                continue
            if state.run_status.value in {"completed", "blocked"}:
                return state, runner.inspect()

    def test_acetic_acid_and_sulfuric_acid_complete_generic_pipeline(self):
        acetic_inspect = self._run_benchmark("examples/acetic_acid_india_mock.yaml")
        sulfuric_inspect = self._run_benchmark("examples/sulfuric_acid_india_mock.yaml")
        self.assertIn("method_decisions:", acetic_inspect)
        self.assertIn("method_decisions:", sulfuric_inspect)
        self.assertIn("family_adapter:", acetic_inspect)
        self.assertIn("family_adapter:", sulfuric_inspect)
        self.assertIn("sparse_data_policy:", acetic_inspect)
        self.assertIn("sparse_data_policy:", sulfuric_inspect)
        self.assertIn("capacity_case", acetic_inspect)
        self.assertIn("capacity_case", sulfuric_inspect)

    def test_sodium_bicarbonate_uses_solids_layout_and_decisions(self):
        inspect_text = self._run_benchmark("examples/sodium_bicarbonate_india_mock.yaml")
        self.assertIn("solids_crystallization_train", inspect_text)
        self.assertIn("storage_choice", inspect_text)
        self.assertIn("layout:", inspect_text)

    def test_phenol_completes_with_oxidation_route_family_coverage(self):
        inspect_text = self._run_benchmark("examples/phenol_india_mock.yaml")
        self.assertIn("benchmark:", inspect_text)
        self.assertIn("phenol", inspect_text)
        self.assertIn("route[cumene_oxidation_cleavage]: family=oxidation_recovery_train", inspect_text)
        self.assertIn("route_family_id: oxidation_recovery_train", inspect_text)
        self.assertIn("trickle_bed_oxidizer", inspect_text)
        self.assertIn("critic_registry:", inspect_text)

    def test_para_nitroanisole_blocks_honestly_at_evidence_lock(self):
        state, inspect_text = self._run_expected_block("examples/pna_project.yaml")
        self.assertEqual(state.run_status.value, "blocked")
        self.assertEqual(state.current_stage_id, "literature_route_survey")
        self.assertEqual(state.blocked_stage_id, "literature_route_survey")
        self.assertIn("benchmark:", inspect_text)
        self.assertIn("para_nitroanisole", inspect_text)
        self.assertIn("specialty_aromatic_separation_intensive", inspect_text)
        self.assertIn("report_acceptance:", inspect_text)
        self.assertIn("overall_status: blocked", inspect_text)
        self.assertIn("pipeline_status: blocked", inspect_text)
        self.assertIn("missing_route_species_graph", inspect_text)
        self.assertIn("invalid_core_species", inspect_text)
        self.assertIn("species_blocking_routes: none", inspect_text)
        self.assertIn("route_chemistry:", inspect_text)
        self.assertIn("anonymous_species_count: 3", inspect_text)
        self.assertIn("agent_fabric:", inspect_text)
        self.assertIn("critic_registry:", inspect_text)

    def test_benzalkonium_chloride_advances_past_generic_route_discovery(self):
        config = ProjectConfig(
            project_id="benzalkonium-chloride-test",
            basis=ProjectBasis(
                target_product="Benzalkonium chloride",
                capacity_tpa=50000,
                target_purity_wt_pct=80.0,
                operating_mode="continuous",
                throughput_basis="finished_product",
                nominal_active_wt_pct=80.0,
                product_form="aqueous_or_alcohol_solution",
                carrier_components=["water", "ethanol"],
                homolog_distribution={"c12": 0.4, "c14": 0.5, "c16": 0.1},
                quality_targets=[
                    "Residual free benzyl chloride below finished-goods limit",
                    "Residual free tertiary amine below finished-goods limit",
                ],
            ),
            model=ModelSettings(backend="mock", model_name="gemini-3.1-pro-preview", temperature=0.2),
        )
        config.output_root = self.temp_dir
        runner = PipelineRunner(config)
        state = runner.run()
        inspect_text = runner.inspect()
        self.assertNotEqual(state.blocked_stage_id, "literature_route_survey", msg=inspect_text)
        self.assertIn("process_selection_logic:", inspect_text)
        self.assertIn("discovered_routes: 3", inspect_text)
        self.assertIn("route_chemistry:", inspect_text)
        self.assertIn("blocking_routes: none", inspect_text)


if __name__ == "__main__":
    unittest.main()
