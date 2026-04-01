import unittest

from aoc.models import SeparationPacket, StreamComponentFlow, StreamRecord
from aoc.solvers.recycle_network import build_recycle_network_packets


class RecycleNetworkTests(unittest.TestCase):
    def test_build_recycle_network_packets_emits_multiple_loops_and_purge_policy(self):
        streams = [
            StreamRecord(
                stream_id="S-301",
                description="Condensate recycle",
                temperature_c=90.0,
                pressure_bar=1.1,
                components=[
                    StreamComponentFlow(name="Water", mass_flow_kg_hr=900.0, molar_flow_kmol_hr=49.95),
                    StreamComponentFlow(name="Ethylene oxide", mass_flow_kg_hr=20.0, molar_flow_kmol_hr=0.454),
                ],
                source_unit_id="concentration",
                destination_unit_id="feed_prep",
                phase_hint="liquid",
            ),
            StreamRecord(
                stream_id="S-401",
                description="Light ends recycle",
                temperature_c=45.0,
                pressure_bar=1.0,
                components=[
                    StreamComponentFlow(name="Water", mass_flow_kg_hr=80.0, molar_flow_kmol_hr=4.441),
                    StreamComponentFlow(name="Ethylene oxide", mass_flow_kg_hr=40.0, molar_flow_kmol_hr=0.908),
                ],
                source_unit_id="purification",
                destination_unit_id="feed_prep",
                phase_hint="mixed",
            ),
            StreamRecord(
                stream_id="S-403",
                description="Purge and heavy ends",
                temperature_c=55.0,
                pressure_bar=1.0,
                components=[
                    StreamComponentFlow(name="Water", mass_flow_kg_hr=10.0, molar_flow_kmol_hr=0.555),
                    StreamComponentFlow(name="Heavy ends", mass_flow_kg_hr=50.0, molar_flow_kmol_hr=0.600),
                ],
                source_unit_id="purification",
                destination_unit_id="waste_treatment",
                phase_hint="mixed",
            ),
        ]
        recycle_solution = {
            "Water": {"total_flow": 60.0, "fresh_flow": 5.0, "recycle_flow": 54.0, "purge_flow": 1.0, "iterations": 4, "converged": True},
            "Ethylene oxide": {"total_flow": 1.5, "fresh_flow": 0.2, "recycle_flow": 1.1, "purge_flow": 0.2, "iterations": 5, "converged": True},
        }

        packets, summaries = build_recycle_network_packets(streams, recycle_solution, 0.5, ["s1"], [])

        self.assertEqual(len(packets), 2)
        self.assertEqual(len(summaries), 2)
        self.assertTrue({"concentration_recycle_loop", "purification_recycle_loop"}.issubset({packet.loop_id for packet in packets}))
        self.assertTrue(all(packet.purge_policy_by_family for packet in packets))
        purification_summary = next(summary for summary in summaries if summary.loop_id == "purification_recycle_loop")
        self.assertIn("heavy_byproducts", purification_summary.purge_policy_by_family)
        self.assertGreaterEqual(purification_summary.max_iterations, 1)

    def test_recycle_network_uses_nonideal_separator_packet_to_recover_cleanup_components(self):
        streams = [
            StreamRecord(
                stream_id="S-401",
                description="Light ends recycle",
                temperature_c=45.0,
                pressure_bar=1.0,
                components=[
                    StreamComponentFlow(name="Benzyl chloride", mass_flow_kg_hr=60.0, molar_flow_kmol_hr=0.474),
                ],
                source_unit_id="purification",
                destination_unit_id="feed_prep",
                phase_hint="liquid",
            ),
            StreamRecord(
                stream_id="S-403",
                description="Purge and heavy ends",
                temperature_c=55.0,
                pressure_bar=1.0,
                components=[
                    StreamComponentFlow(name="Benzyl chloride", mass_flow_kg_hr=20.0, molar_flow_kmol_hr=0.158),
                ],
                source_unit_id="purification",
                destination_unit_id="waste_treatment",
                phase_hint="liquid",
            ),
        ]
        recycle_solution = {
            "Benzyl chloride": {"total_flow": 0.632, "fresh_flow": 0.632, "recycle_flow": 0.0, "purge_flow": 0.0, "iterations": 2, "converged": True},
        }
        separation_packets = [
            SeparationPacket(
                packet_id="purification_packet",
                unit_id="purification",
                separation_family="distillation",
                driving_force="temperature/volatility",
                component_split_to_recycle={"Benzyl chloride": 0.75},
                component_split_to_waste={"Benzyl chloride": 0.25},
                equilibrium_model="modified_raoult_nrtl_family_estimated",
                activity_model="nrtl_family_estimated_modified_raoult",
            )
        ]

        packets, _ = build_recycle_network_packets(
            streams,
            recycle_solution,
            0.5,
            ["s1"],
            [],
            separation_packets=separation_packets,
        )

        purification_packet = next(packet for packet in packets if packet.loop_id == "purification_recycle_loop")
        self.assertGreater(purification_packet.component_recycle_kmol_hr["Benzyl chloride"], 0.0)
        self.assertGreater(purification_packet.component_purge_kmol_hr["Benzyl chloride"], 0.0)
        self.assertLess(purification_packet.component_convergence_error_pct["Benzyl chloride"], 2.0)
        self.assertAlmostEqual(purification_packet.component_recycle_kmol_hr["Benzyl chloride"], 0.474, places=3)
        self.assertAlmostEqual(purification_packet.component_purge_kmol_hr["Benzyl chloride"], 0.158, places=3)


if __name__ == "__main__":
    unittest.main()
