import unittest

from aoc.models import StreamComponentFlow, StreamRecord
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


if __name__ == "__main__":
    unittest.main()
