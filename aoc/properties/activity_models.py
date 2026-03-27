from __future__ import annotations

import math

from aoc.properties.models import BinaryInteractionParameter


def nrtl_activity_coefficients_binary(
    x1: float,
    bip: BinaryInteractionParameter,
) -> tuple[float, float]:
    """Return binary liquid-phase activity coefficients using the NRTL model.

    The stored binary-interaction parameters are treated as dimensionless tau
    values for the current screening-level non-ideal VLE basis.
    """

    x1 = max(min(x1, 0.999999), 0.000001)
    x2 = 1.0 - x1
    tau12 = float(bip.tau12 or 0.0)
    tau21 = float(bip.tau21 or 0.0)
    alpha12 = float(bip.alpha12 if bip.alpha12 is not None else 0.3)

    g12 = math.exp(-alpha12 * tau12)
    g21 = math.exp(-alpha12 * tau21)

    d12 = x2 + x1 * g12
    d21 = x1 + x2 * g21
    d12 = max(d12, 1e-12)
    d21 = max(d21, 1e-12)

    ln_gamma1 = (x2**2) * (
        tau21 * (g21 / d21) ** 2
        + (tau12 * g12) / (d12**2)
    )
    ln_gamma2 = (x1**2) * (
        tau12 * (g12 / d12) ** 2
        + (tau21 * g21) / (d21**2)
    )

    gamma1 = max(min(math.exp(ln_gamma1), 100.0), 1e-6)
    gamma2 = max(min(math.exp(ln_gamma2), 100.0), 1e-6)
    return gamma1, gamma2


def activity_coefficients_binary(
    model_name: str,
    x1: float,
    bip: BinaryInteractionParameter,
) -> tuple[float, float]:
    model = (model_name or bip.model_name or "NRTL").strip().lower()
    if model == "nrtl":
        return nrtl_activity_coefficients_binary(x1, bip)
    raise ValueError(f"Unsupported activity model '{model_name}'.")
