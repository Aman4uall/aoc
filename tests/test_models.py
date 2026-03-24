import unittest

from aoc.models import ProcessTemplate, ProjectBasis, ProjectConfig, UserDocument


class ModelTests(unittest.TestCase):
    def test_project_config_round_trip(self):
        config = ProjectConfig(
            project_id="demo",
            basis=ProjectBasis(
                target_product="Ethylene Glycol",
                capacity_tpa=200000,
                target_purity_wt_pct=99.9,
                process_template=ProcessTemplate.ETHYLENE_GLYCOL_INDIA,
                india_only=True,
            ),
            user_documents=[UserDocument(label="Doc", path="/tmp/doc.md")],
        )
        data = config.model_dump()
        restored = ProjectConfig.model_validate(data)
        self.assertEqual(restored.project_id, "demo")
        self.assertEqual(restored.basis.target_product, "Ethylene Glycol")
        self.assertEqual(restored.basis.process_template, ProcessTemplate.ETHYLENE_GLYCOL_INDIA)
        self.assertEqual(restored.user_documents[0].label, "Doc")
