import unittest

from aoc.document_facts import extract_document_facts
from aoc.flowsheet_blueprint import build_process_narrative_from_blueprint, build_unit_train_candidate_set, select_flowsheet_blueprint
from aoc.models import ReactionParticipant, RouteOption, RouteSurveyArtifact
from aoc.route_chemistry import build_route_chemistry_artifact
from aoc.route_families import build_route_family_artifact


class FlowsheetBlueprintTests(unittest.TestCase):
    def test_document_route_builds_tagged_unit_train_blueprint(self):
        facts = extract_document_facts(
            "user_doc_1",
            "Ibuprofen benchmark",
            "\n".join(
                [
                    "Process 4",
                    "Isobutyl benzene is raw material. Hydrogen peroxide oxidation gets Ibuprofen. Yield of the process is 88%.",
                    "Suggested Site",
                    "Ludhiana, Punjab",
                    "Reactor R003 is a batch stirred tank reactor.",
                    "Distillation Column-DC001",
                    "Plug Flow Reactor-PFR",
                ]
            ),
            "Ibuprofen",
        )
        route = RouteOption(
            route_id="user_doc_1_process_4",
            name="Process 4",
            reaction_equation="Isobutyl benzene + Hydrogen peroxide -> Ibuprofen",
            participants=[
                ReactionParticipant(name="Isobutyl benzene", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                ReactionParticipant(name="Hydrogen peroxide", formula="", coefficient=1.0, role="reactant", molecular_weight_g_mol=0.0),
                ReactionParticipant(name="Ibuprofen", formula="", coefficient=1.0, role="product", molecular_weight_g_mol=0.0),
            ],
            route_origin="document",
            source_document_id="user_doc_1",
            evidence_score=0.90,
            chemistry_completeness_score=0.82,
            separation_complexity_score=0.58,
            extracted_species=["Isobutyl benzene", "Hydrogen peroxide", "Ibuprofen"],
            reaction_family_hints=["oxidation"],
            catalysts=[],
            operating_temperature_c=80.0,
            operating_pressure_bar=3.0,
            residence_time_hr=4.0,
            yield_fraction=0.88,
            selectivity_fraction=0.90,
            separations=["distillation purification"],
            scale_up_notes="Document-derived route option.",
            route_score=8.8,
            rationale="Process 4 is selected in the document.",
            citations=["user_doc_1"],
        )
        survey = RouteSurveyArtifact(routes=[route], markdown="", citations=["user_doc_1"])
        route_chemistry = build_route_chemistry_artifact(survey, [facts])
        route_families = build_route_family_artifact(survey)
        candidate_set = build_unit_train_candidate_set(survey, route_chemistry, route_families, [facts], "batch")
        blueprint = select_flowsheet_blueprint(candidate_set, route.route_id)
        narrative = build_process_narrative_from_blueprint(blueprint)

        self.assertEqual(len(candidate_set.blueprints), 1)
        self.assertTrue(blueprint.steps)
        self.assertTrue(any(step.step_role == "reaction" for step in blueprint.steps))
        self.assertTrue(any(step.unit_tag in {"PFR", "R003", "DC001"} for step in blueprint.steps if step.unit_tag))
        self.assertIn("### Route-to-Unit Mapping", narrative.markdown)
        self.assertIn("graph TD", narrative.bfd_mermaid)


if __name__ == "__main__":
    unittest.main()
