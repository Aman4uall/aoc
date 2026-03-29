import unittest

from aoc.critics import merge_critic_registry
from aoc.models import Severity, SolveResult, ValidationIssue


class CriticRegistryTests(unittest.TestCase):
    def test_merge_critic_registry_collects_issues_and_solver_messages(self):
        registry = merge_critic_registry(
            None,
            "energy_balance",
            [
                ValidationIssue(
                    code="weak_nonideal_thermo_basis",
                    severity=Severity.WARNING,
                    message="Ideal fallback still active.",
                    artifact_ref="separation_thermo",
                ),
                ValidationIssue(
                    code="route_cost_mismatch",
                    severity=Severity.BLOCKED,
                    message="Route and cost model disagree.",
                    artifact_ref="cost_model",
                ),
            ],
            solve_result=SolveResult(
                case_id="case",
                critic_messages=["Recycle loop remains weakly conditioned."],
                citations=["s1"],
                assumptions=["seed"],
                markdown="seed",
            ),
        )
        self.assertEqual(registry.warning_count, 2)
        self.assertEqual(registry.blocked_count, 1)
        self.assertIn("weak_nonideal_thermo_basis", registry.markdown)
        self.assertIn("solve_result_critic_message", registry.markdown)


if __name__ == "__main__":
    unittest.main()
