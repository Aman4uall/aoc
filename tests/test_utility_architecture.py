import unittest

from aoc.models import DecisionRecord, HeatIntegrationCase, HeatMatch, HeatStream, UtilityNetworkDecision, UtilityTarget
from aoc.utility_architecture import build_utility_architecture_decision


class UtilityArchitectureTests(unittest.TestCase):
    def test_island_aware_selection_balances_recovery_across_disconnected_islands(self):
        decision = UtilityNetworkDecision(
            route_id="test_route",
            utility_target=UtilityTarget(
                base_hot_utility_kw=180.0,
                base_cold_utility_kw=160.0,
                minimum_hot_utility_kw=40.0,
                minimum_cold_utility_kw=50.0,
                recoverable_duty_kw=120.0,
                pinch_temp_c=118.0,
            ),
            heat_streams=[
                HeatStream(stream_id="H1", name="Reactor effluent", kind="hot", source_unit_id="reactor", supply_temp_c=180.0, target_temp_c=120.0, duty_kw=100.0),
                HeatStream(stream_id="C1", name="Column reboiler", kind="cold", source_unit_id="purification", supply_temp_c=90.0, target_temp_c=150.0, duty_kw=90.0),
                HeatStream(stream_id="H2", name="Concentrator overhead", kind="hot", source_unit_id="concentration", supply_temp_c=140.0, target_temp_c=80.0, duty_kw=80.0),
                HeatStream(stream_id="C2", name="Dryer preheat", kind="cold", source_unit_id="drying", supply_temp_c=40.0, target_temp_c=95.0, duty_kw=70.0),
            ],
            cases=[
                HeatIntegrationCase(
                    case_id="test_route_direct",
                    title="Direct recovery",
                    recovered_duty_kw=120.0,
                    residual_hot_utility_kw=60.0,
                    residual_cold_utility_kw=40.0,
                    added_capex_inr=10_000_000.0,
                    annual_savings_inr=5_000_000.0,
                    payback_years=2.0,
                    operability_penalty=0.05,
                    safety_penalty=0.02,
                    heat_matches=[
                        HeatMatch(
                            match_id="match_1",
                            hot_stream_id="H1",
                            cold_stream_id="C1",
                            recovered_duty_kw=85.0,
                            direct=True,
                            medium="direct",
                            min_approach_temp_c=20.0,
                        ),
                        HeatMatch(
                            match_id="match_2",
                            hot_stream_id="H2",
                            cold_stream_id="C2",
                            recovered_duty_kw=60.0,
                            direct=True,
                            medium="direct",
                            min_approach_temp_c=20.0,
                        ),
                    ],
                )
            ],
            decision=DecisionRecord(
                decision_id="utility_network_decision",
                context="test utility architecture",
                selected_candidate_id="test_route_direct",
                selected_summary="Direct recovery selected for test basis.",
                confidence=0.8,
            ),
            selected_case_id="test_route_direct",
            base_annual_utility_cost_inr=12_000_000.0,
            selected_annual_utility_cost_inr=7_000_000.0,
            markdown="test",
        )

        utility_architecture = build_utility_architecture_decision(decision)
        selected_case = next(
            case
            for case in utility_architecture.architecture.cases
            if case.case_id == utility_architecture.architecture.selected_case_id
        )

        self.assertEqual(len(selected_case.utility_islands), 2)
        self.assertEqual(len(utility_architecture.architecture.selected_island_ids), 2)
        self.assertEqual(len({step.island_id for step in utility_architecture.architecture.selected_train_steps}), 2)
        self.assertTrue(all(island.target_recovered_duty_kw > 0.0 for island in selected_case.utility_islands))
        self.assertTrue(all(island.recoverable_potential_kw >= island.target_recovered_duty_kw for island in selected_case.utility_islands))
        self.assertAlmostEqual(
            sum(island.recovered_duty_kw for island in selected_case.utility_islands),
            sum(step.recovered_duty_kw for step in utility_architecture.architecture.selected_train_steps),
            places=3,
        )
        self.assertLessEqual(
            abs(sum(step.recovered_duty_kw for step in utility_architecture.architecture.selected_train_steps) - 120.0),
            1.0,
        )

    def test_richer_network_architecture_cases_are_generated_for_complex_recovery_topology(self):
        decision = UtilityNetworkDecision(
            route_id="complex_route",
            utility_target=UtilityTarget(
                base_hot_utility_kw=260.0,
                base_cold_utility_kw=220.0,
                minimum_hot_utility_kw=70.0,
                minimum_cold_utility_kw=60.0,
                recoverable_duty_kw=150.0,
                pinch_temp_c=122.0,
            ),
            heat_streams=[
                HeatStream(stream_id="H1", name="Regenerator overhead", kind="hot", source_unit_id="regeneration", supply_temp_c=190.0, target_temp_c=120.0, duty_kw=95.0),
                HeatStream(stream_id="H2", name="Concentrator vapor", kind="hot", source_unit_id="concentration", supply_temp_c=150.0, target_temp_c=85.0, duty_kw=80.0),
                HeatStream(stream_id="C1", name="Purification reboiler", kind="cold", source_unit_id="purification", supply_temp_c=95.0, target_temp_c=170.0, duty_kw=90.0),
                HeatStream(stream_id="C2", name="Dryer preheat", kind="cold", source_unit_id="drying", supply_temp_c=55.0, target_temp_c=125.0, duty_kw=70.0),
            ],
            cases=[
                HeatIntegrationCase(
                    case_id="complex_route_htm",
                    title="HTM recovery basis",
                    recovered_duty_kw=150.0,
                    residual_hot_utility_kw=80.0,
                    residual_cold_utility_kw=70.0,
                    added_capex_inr=14_000_000.0,
                    annual_savings_inr=6_200_000.0,
                    payback_years=2.3,
                    operability_penalty=0.06,
                    safety_penalty=0.03,
                    heat_matches=[
                        HeatMatch(
                            match_id="m1",
                            hot_stream_id="H1",
                            cold_stream_id="C1",
                            recovered_duty_kw=82.0,
                            direct=False,
                            medium="Dowtherm A",
                            min_approach_temp_c=20.0,
                        ),
                        HeatMatch(
                            match_id="m2",
                            hot_stream_id="H2",
                            cold_stream_id="C2",
                            recovered_duty_kw=64.0,
                            direct=False,
                            medium="Dowtherm A",
                            min_approach_temp_c=20.0,
                        ),
                    ],
                )
            ],
            decision=DecisionRecord(
                decision_id="utility_network_decision",
                context="complex utility architecture",
                selected_candidate_id="complex_route_htm",
                selected_summary="HTM recovery selected for test basis.",
                confidence=0.82,
            ),
            selected_case_id="complex_route_htm",
            base_annual_utility_cost_inr=14_500_000.0,
            selected_annual_utility_cost_inr=8_100_000.0,
            markdown="test",
        )

        utility_architecture = build_utility_architecture_decision(decision)
        case_index = {case.case_id: case for case in utility_architecture.architecture.cases}

        self.assertIn("complex_route_htm__shared_htm", case_index)
        self.assertIn("complex_route_htm__cond_reb_cluster", case_index)
        self.assertIn("complex_route_htm__staged_headers", case_index)

        shared_case = case_index["complex_route_htm__shared_htm"]
        cluster_case = case_index["complex_route_htm__cond_reb_cluster"]
        staged_case = case_index["complex_route_htm__staged_headers"]

        self.assertGreater(shared_case.shared_htm_island_count, 0)
        self.assertGreater(cluster_case.condenser_reboiler_cluster_count, 0)
        self.assertGreater(staged_case.header_count, 0)
        self.assertTrue(any(island.shared_htm_inventory_m3 > 0.0 for island in shared_case.utility_islands))
        self.assertTrue(any(island.header_design_pressure_bar > 0.0 for island in staged_case.utility_islands))
        self.assertTrue(any(island.condenser_reboiler_pair_score > 0.0 for island in cluster_case.utility_islands))
        self.assertTrue(any(step.header_level > 0 for step in staged_case.selected_train_steps))
        self.assertTrue(any(step.cluster_id for step in cluster_case.selected_train_steps))
        self.assertTrue(
            any(
                item.package_role == "header"
                for step in staged_case.selected_train_steps
                for item in step.package_items
            )
        )


if __name__ == "__main__":
    unittest.main()
