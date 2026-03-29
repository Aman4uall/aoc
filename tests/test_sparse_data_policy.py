import shutil
import tempfile
import unittest
from pathlib import Path

from aoc.archetypes import classify_process_archetype
from aoc.config import load_project_config
from aoc.decision_engine import resolve_property_gaps
from aoc.family_adapters import build_chemistry_family_adapter
from aoc.models import ChemistryFamilyAdapter
from aoc.properties import build_property_package_artifact
from aoc.reasoning import build_reasoning_service
from aoc.research import ResearchManager
from aoc.sparse_data import build_sparse_data_policy
from aoc.validators import validate_sparse_data_policy_for_stage


class SparseDataPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aoc-sparse-policy-")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _config(self, filename: str):
        config = load_project_config(str(Path("examples", filename).resolve()))
        config.output_root = self.temp_dir
        return config

    def test_missing_binary_interaction_pairs_stay_warning_only_for_liquid_vle_family(self):
        config = self._config("ethylene_glycol_india_mock.yaml")
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        property_gap = resolve_property_gaps(profile, config)
        archetype = classify_process_archetype(config, survey, property_gap)
        adapter = build_chemistry_family_adapter(config, survey, property_gap, archetype)
        packages = build_property_package_artifact(config, bundle, profile, survey).model_copy(
            update={"unresolved_binary_pairs": ["water__ethylene_glycol"]},
            deep=True,
        )
        policy = build_sparse_data_policy(config, adapter, packages)
        bip_rule = next(rule for rule in policy.rules if rule.subject == "binary_interaction_parameters")
        self.assertEqual(bip_rule.current_status, "warning")
        self.assertNotIn("distillation_design", policy.blocked_stage_ids)
        warning_issues = validate_sparse_data_policy_for_stage("distillation_design", policy)
        self.assertTrue(any(issue.severity.value == "warning" for issue in warning_issues))

    def test_missing_henry_basis_blocks_absorber_family_detail_stage(self):
        config = self._config("ethylene_glycol_india_mock.yaml")
        reasoning = build_reasoning_service(config.model)
        bundle = ResearchManager(reasoning).build_bundle(config)
        profile = reasoning.build_product_profile(config.basis, bundle.sources, bundle.corpus_excerpt)
        survey = reasoning.survey_routes(config.basis, bundle.sources, bundle.corpus_excerpt)
        adapter = ChemistryFamilyAdapter(
            adapter_id="inorganic_absorption_conversion_train",
            family_label="Inorganic Absorption and Conversion Train",
            compound_family="inorganic",
            dominant_phase_system="mixed",
            route_generation_hints=["absorption"],
            property_priority_order=["henry_constants", "liquid_density"],
            preferred_reactor_candidates=["fixed_bed_converter"],
            preferred_separation_candidates=["absorption_train"],
            preferred_storage_candidates=["vertical_tank_farm"],
            moc_bias_candidates=["rubber_lined_cs"],
            common_unit_operations=["converter", "absorber"],
            corrosion_cues=["acid_service"],
            heat_integration_patterns=["waste_heat_boiler"],
            critic_focus=["henry_law_basis"],
            sparse_data_blockers=["missing_henry_constant"],
            benchmark_profiles=["sulfuric_acid"],
            rationale="Synthetic absorption adapter for sparse-data policy coverage test.",
            markdown="absorption adapter",
        )
        packages = build_property_package_artifact(config, bundle, profile, survey).model_copy(
            update={"unresolved_henry_pairs": ["sulfur_dioxide__water"]},
            deep=True,
        )
        policy = build_sparse_data_policy(config, adapter, packages)
        henry_rule = next(rule for rule in policy.rules if rule.subject == "henry_constants")
        self.assertEqual(henry_rule.current_status, "blocked")
        self.assertIn("distillation_design", policy.blocked_stage_ids)
        blocked_issues = validate_sparse_data_policy_for_stage("distillation_design", policy)
        self.assertTrue(any(issue.severity.value == "blocked" for issue in blocked_issues))


if __name__ == "__main__":
    unittest.main()
