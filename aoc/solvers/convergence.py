from __future__ import annotations


def solve_recycle_loop(
    target_total_flow: float,
    consumed_flow: float,
    recovery_fraction: float,
    purge_fraction: float,
    tolerance: float = 1e-6,
    max_iterations: int = 50,
) -> dict[str, float | int | bool]:
    recovery_fraction = max(0.0, min(recovery_fraction, 0.999))
    purge_fraction = max(0.0, min(purge_fraction, 0.999))
    fresh = max(target_total_flow, 0.0)
    recycle = 0.0
    for iteration in range(1, max_iterations + 1):
        total = fresh + recycle
        unreacted = max(total - consumed_flow, 0.0)
        recovered = unreacted * recovery_fraction
        new_recycle = recovered * (1.0 - purge_fraction)
        new_fresh = max(target_total_flow - new_recycle, 0.0)
        if abs(new_recycle - recycle) <= tolerance and abs(new_fresh - fresh) <= tolerance:
            recycle = new_recycle
            fresh = new_fresh
            break
        recycle = new_recycle
        fresh = new_fresh
    total = fresh + recycle
    unreacted = max(total - consumed_flow, 0.0)
    recovered = unreacted * recovery_fraction
    purge = recovered * purge_fraction + max(unreacted - recovered, 0.0)
    return {
        "fresh_flow": fresh,
        "recycle_flow": recycle,
        "purge_flow": purge,
        "total_flow": total,
        "iterations": iteration,
        "converged": iteration < max_iterations,
    }
