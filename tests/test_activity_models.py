import unittest

from aoc.properties.activity_models import nrtl_activity_coefficients_binary
from aoc.properties.models import BinaryInteractionParameter


class ActivityModelTests(unittest.TestCase):
    def test_nrtl_activity_coefficients_binary_returns_nonideal_gamma(self):
        bip = BinaryInteractionParameter(
            bip_id="water__acetic_acid",
            component_a_id="water",
            component_b_id="acetic_acid",
            component_a_name="Water",
            component_b_name="Acetic acid",
            model_name="NRTL",
            tau12=0.42,
            tau21=-0.18,
            alpha12=0.30,
            source_ids=["src_bip"],
        )
        gamma1, gamma2 = nrtl_activity_coefficients_binary(0.5, bip)
        self.assertGreater(gamma1, 0.0)
        self.assertGreater(gamma2, 0.0)
        self.assertNotAlmostEqual(gamma1, 1.0, places=6)
        self.assertNotAlmostEqual(gamma2, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
