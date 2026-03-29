import unittest

from aoc.mechanical import (
    build_mechanical_design_artifact,
    build_mechanical_design_basis,
    build_vessel_mechanical_designs,
)
from aoc.models import EquipmentListArtifact, EquipmentSpec


class MechanicalDesignTests(unittest.TestCase):
    def test_mechanical_design_emits_load_cases_platforms_and_nozzle_classes(self):
        equipment = EquipmentListArtifact(
            items=[
                EquipmentSpec(
                    equipment_id="C-101",
                    equipment_type="Absorber",
                    service="Gas absorption",
                    design_basis="Packed absorber basis",
                    volume_m3=42.0,
                    design_temperature_c=85.0,
                    design_pressure_bar=7.5,
                    material_of_construction="SS316L",
                    duty_kw=180.0,
                    citations=["s1"],
                ),
                EquipmentSpec(
                    equipment_id="HDR-201",
                    equipment_type="Utility header",
                    service="Shared HTM header",
                    design_basis="Shared HTM island header",
                    volume_m3=3.0,
                    design_temperature_c=220.0,
                    design_pressure_bar=13.0,
                    material_of_construction="Carbon steel",
                    duty_kw=320.0,
                    citations=["s1"],
                ),
            ],
            citations=["s1"],
        )

        artifact = build_mechanical_design_artifact(equipment)
        basis = build_mechanical_design_basis(artifact)
        vessel_designs = build_vessel_mechanical_designs(artifact)

        absorber = next(item for item in artifact.items if item.equipment_id == "C-101")
        header = next(item for item in artifact.items if item.equipment_id == "HDR-201")
        header_vessel = next(item for item in vessel_designs if item.equipment_id == "HDR-201")

        self.assertTrue(absorber.support_load_case)
        self.assertTrue(absorber.maintenance_platform_required)
        self.assertGreater(absorber.platform_area_m2, 0.0)
        self.assertTrue(absorber.pressure_class)
        self.assertGreaterEqual(absorber.hydrotest_pressure_bar, absorber.design_pressure_bar)
        self.assertGreater(absorber.wind_load_kn, 0.0)
        self.assertGreater(absorber.seismic_load_kn, 0.0)
        self.assertTrue(absorber.support_variant)
        self.assertGreater(absorber.anchor_group_count, 0)
        self.assertGreater(absorber.foundation_footprint_m2, 0.0)
        self.assertGreater(absorber.maintenance_clearance_m, 0.0)
        self.assertTrue(absorber.nozzle_reinforcement_family)
        self.assertGreaterEqual(absorber.local_shell_load_interaction_factor, 1.0)

        self.assertEqual(header.support_type, "pipe rack support")
        self.assertEqual(header.support_variant, "guided rack shoe")
        self.assertTrue(header.pipe_rack_tie_in_required)
        self.assertGreater(header.piping_load_kn, 0.0)
        self.assertGreater(header.nozzle_diameter_mm, 80.0)
        self.assertEqual(header_vessel.nozzle_schedule.nozzle_pressure_class, header.pressure_class)
        self.assertTrue(header_vessel.nozzle_schedule.nozzle_connection_classes)
        self.assertTrue(header_vessel.nozzle_schedule.nozzle_orientations_deg)
        self.assertTrue(header_vessel.nozzle_schedule.nozzle_projection_mm)
        self.assertTrue(header_vessel.nozzle_schedule.local_shell_load_factors)
        self.assertTrue(header_vessel.support_design.foundation_note)
        self.assertGreater(header_vessel.support_design.foundation_footprint_m2, 0.0)

        self.assertTrue(basis.support_design_basis)
        self.assertTrue(basis.load_case_basis)
        self.assertTrue(basis.foundation_basis)
        self.assertTrue(basis.nozzle_load_basis)
        self.assertTrue(basis.connection_rating_basis)
        self.assertTrue(basis.access_platform_basis)


if __name__ == "__main__":
    unittest.main()
