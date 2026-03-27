import unittest

from aoc.calculators import build_reaction_system
from aoc.models import KineticAssessmentArtifact, ProjectBasis, ReactionParticipant, RouteOption
from aoc.pipeline import validate_reaction_system


class ReactionNetworkTests(unittest.TestCase):
    def _kinetics(self) -> KineticAssessmentArtifact:
        return KineticAssessmentArtifact(
            feasible=True,
            activation_energy_kj_per_mol=40.0,
            pre_exponential_factor=1.0e6,
            apparent_order=1.0,
            design_residence_time_hr=1.5,
            markdown="seed",
            citations=["s1"],
        )

    def test_declared_byproducts_create_non_blocking_closure(self):
        basis = ProjectBasis(target_product="Acetic Acid", capacity_tpa=100000, target_purity_wt_pct=99.5, india_only=True)
        route = RouteOption(
            route_id="methanol_carbonylation",
            name="Methanol carbonylation",
            reaction_equation="CH3OH + CO -> C2H4O2",
            participants=[
                ReactionParticipant(name="Methanol", formula="CH4O", coefficient=1.0, role="reactant", molecular_weight_g_mol=32.04, phase="liquid"),
                ReactionParticipant(name="Carbon monoxide", formula="CO", coefficient=1.0, role="reactant", molecular_weight_g_mol=28.01, phase="gas"),
                ReactionParticipant(name="Acetic acid", formula="C2H4O2", coefficient=1.0, role="product", molecular_weight_g_mol=60.05, phase="liquid"),
            ],
            catalysts=["rhodium"],
            operating_temperature_c=185.0,
            operating_pressure_bar=30.0,
            residence_time_hr=1.5,
            yield_fraction=0.95,
            selectivity_fraction=0.98,
            byproducts=["trace propionic acid"],
            separations=["flash", "distillation"],
            scale_up_notes="",
            route_score=9.0,
            rationale="",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, self._kinetics(), ["s1"], [])
        self.assertIsNotNone(reaction_system.byproduct_closure)
        self.assertEqual(reaction_system.byproduct_closure.closure_status, "estimated")
        self.assertFalse(reaction_system.byproduct_closure.blocking)
        self.assertTrue(reaction_system.byproduct_closure.estimates)
        self.assertEqual(validate_reaction_system(reaction_system), [])

    def test_large_gap_without_byproduct_basis_blocks(self):
        basis = ProjectBasis(target_product="Generic Product", capacity_tpa=25000, target_purity_wt_pct=98.0, india_only=True)
        route = RouteOption(
            route_id="weak_route",
            name="Weakly defined route",
            reaction_equation="A + B -> P",
            participants=[
                ReactionParticipant(name="A", formula="C2H4", coefficient=1.0, role="reactant", molecular_weight_g_mol=28.05, phase="gas"),
                ReactionParticipant(name="B", formula="H2O", coefficient=1.0, role="reactant", molecular_weight_g_mol=18.015, phase="liquid"),
                ReactionParticipant(name="P", formula="C2H6O", coefficient=1.0, role="product", molecular_weight_g_mol=46.07, phase="liquid"),
            ],
            catalysts=[],
            operating_temperature_c=120.0,
            operating_pressure_bar=8.0,
            residence_time_hr=2.0,
            yield_fraction=0.70,
            selectivity_fraction=0.82,
            separations=["flash"],
            scale_up_notes="",
            route_score=5.0,
            rationale="",
            citations=["s1"],
        )
        reaction_system = build_reaction_system(basis, route, self._kinetics(), ["s1"], [])
        self.assertTrue(reaction_system.byproduct_closure.blocking)
        self.assertEqual(reaction_system.byproduct_closure.closure_status, "blocked")
        self.assertTrue(any(issue.code == "blocked_byproduct_closure" for issue in validate_reaction_system(reaction_system)))


if __name__ == "__main__":
    unittest.main()
