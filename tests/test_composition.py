import unittest

from aoc.models import StreamComponentFlow, StreamRecord, UnitOperationPacket
from aoc.solvers.composition import build_unit_composition_artifacts, composition_state_for_unit, estimate_bulk_cp_kj_kg_k


class CompositionPropagationTests(unittest.TestCase):
    def test_build_unit_composition_artifacts_emits_state_and_closure(self):
        streams = [
            StreamRecord(
                stream_id="S-1",
                description="Feed",
                temperature_c=25.0,
                pressure_bar=1.0,
                components=[
                    StreamComponentFlow(name="Water", mass_flow_kg_hr=900.0, molar_flow_kmol_hr=49.95),
                    StreamComponentFlow(name="Ethylene oxide", mass_flow_kg_hr=100.0, molar_flow_kmol_hr=2.27),
                ],
                source_unit_id="feed_prep",
                destination_unit_id="reactor",
                phase_hint="liquid",
            ),
            StreamRecord(
                stream_id="S-2",
                description="Reactor outlet",
                temperature_c=180.0,
                pressure_bar=10.0,
                components=[
                    StreamComponentFlow(name="Water", mass_flow_kg_hr=850.0, molar_flow_kmol_hr=47.18),
                    StreamComponentFlow(name="Ethylene glycol", mass_flow_kg_hr=140.0, molar_flow_kmol_hr=2.26),
                ],
                source_unit_id="reactor",
                destination_unit_id="purification",
                phase_hint="liquid",
            ),
        ]
        packets = [
            UnitOperationPacket(
                packet_id="reactor_unit_packet",
                unit_id="reactor",
                unit_type="reactor",
                service="Reaction zone",
                inlet_stream_ids=["S-1"],
                outlet_stream_ids=["S-2"],
                inlet_mass_flow_kg_hr=1000.0,
                outlet_mass_flow_kg_hr=990.0,
                closure_error_pct=1.0,
                coverage_status="complete",
                status="converged",
            )
        ]

        states, closures = build_unit_composition_artifacts(streams, packets, ["s1"], [])

        self.assertEqual(len(states), 1)
        self.assertEqual(len(closures), 1)
        self.assertEqual(states[0].unit_id, "reactor")
        self.assertIn("Water", states[0].inlet_component_mole_fraction)
        self.assertEqual(closures[0].closure_status, "converged")
        self.assertTrue(closures[0].reactive)
        self.assertGreater(estimate_bulk_cp_kj_kg_k(states[0], 2.5), 2.0)
        self.assertIsNotNone(composition_state_for_unit(states, unit_ids=("reactor",)))


if __name__ == "__main__":
    unittest.main()
