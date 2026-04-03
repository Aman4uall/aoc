from __future__ import annotations

from collections import defaultdict

from aoc.models import ConvergenceSummary, RecyclePacket, SeparationPacket, StreamRecord
from aoc.solvers.convergence import solve_multi_loop_recycle_network


def _aggregate_component_molar(streams: list[StreamRecord]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for stream in streams:
        for component in stream.components:
            totals[component.name] = totals.get(component.name, 0.0) + component.molar_flow_kmol_hr
    return totals


def _classify_impurity_family(component_name: str) -> str:
    lowered = component_name.lower()
    if "water" in lowered:
        return "aqueous_diluent"
    if any(token in lowered for token in ["heavy", "oligomer", "tar", "resin", "glycol"]):
        return "heavy_byproducts"
    if any(token in lowered for token in ["dust", "ash", "salt", "solid", "crystal", "bicarbonate"]):
        return "solids_bleed"
    if any(token in lowered for token in ["air", "nitrogen", "oxygen", "hydrogen", "carbon dioxide", "sulfur dioxide", "sulfur trioxide"]):
        return "light_inerts"
    if any(token in lowered for token in ["oxide", "acid", "ammonia", "solvent", "reactant"]):
        return "recoverable_reactants"
    return "mixed_impurities"


def _component_share(
    component_name: str,
    loop_recycle: dict[str, float],
    total_recycle: dict[str, float],
    loop_purge: dict[str, float],
    total_purge: dict[str, float],
    loop_count: int,
) -> float:
    total_recycle_component = total_recycle.get(component_name, 0.0)
    if total_recycle_component > 1e-9:
        return loop_recycle.get(component_name, 0.0) / total_recycle_component
    total_purge_component = total_purge.get(component_name, 0.0)
    if total_purge_component > 1e-9:
        return loop_purge.get(component_name, 0.0) / total_purge_component
    return 1.0 / max(loop_count, 1)


def _status_from_error(max_component_error: float, overall_closure_error_pct: float, converged: bool) -> str:
    if converged and overall_closure_error_pct <= 2.0 and max_component_error <= 2.0:
        return "converged"
    if overall_closure_error_pct <= 5.0 and max_component_error <= 95.0:
        return "estimated"
    return "blocked"


def _group_streams_by_source(streams: list[StreamRecord], *, recycle: bool) -> dict[str, list[StreamRecord]]:
    grouped: dict[str, list[StreamRecord]] = defaultdict(list)
    for stream in streams:
        if recycle:
            is_recycle = stream.stream_role == "recycle" or stream.destination_unit_id == "feed_prep"
            if not is_recycle or stream.source_unit_id in {None, "battery_limits"}:
                continue
        else:
            is_purge = stream.stream_role in {"purge", "waste", "vent"} or stream.destination_unit_id in {"waste_treatment", "battery_limits"} or "purge" in stream.description.lower()
            if not is_purge or not stream.source_unit_id:
                continue
        grouped[stream.source_unit_id].append(stream)
    return dict(grouped)


def _recommended_min_purge_fraction(section_id: str, family: str) -> float:
    section = section_id.lower()
    if section in {"purification", "primary_recovery"}:
        if family == "heavy_byproducts":
            return 0.12
        if family == "mixed_impurities":
            return 0.06
        if family == "light_inerts":
            return 0.04
    if section in {"crystallization", "solids_finishing"}:
        if family == "solids_bleed":
            return 0.10
        if family == "heavy_byproducts":
            return 0.06
        if family == "aqueous_diluent":
            return 0.02
    if section in {"primary_absorption", "regeneration"}:
        if family == "light_inerts":
            return 0.10
        if family == "recoverable_reactants":
            return 0.02
    return 0.0


def _section_uses_direct_split_closure(section_id: str) -> bool:
    lowered = section_id.lower()
    return lowered in {"purification", "concentration", "primary_recovery", "regeneration", "primary_absorption"}


def build_recycle_network_packets(
    streams: list[StreamRecord],
    recycle_solution: dict[str, dict[str, float | int | bool]],
    overall_closure_error_pct: float,
    citations: list[str],
    assumptions: list[str],
    separation_packets: list[SeparationPacket] | None = None,
) -> tuple[list[RecyclePacket], list[ConvergenceSummary]]:
    recycle_groups = _group_streams_by_source(streams, recycle=True)
    purge_groups = _group_streams_by_source(streams, recycle=False)
    if not recycle_groups:
        return [], []

    total_recycle = _aggregate_component_molar([stream for group in recycle_groups.values() for stream in group])
    total_purge = _aggregate_component_molar([stream for group in purge_groups.values() for stream in group])

    loop_targets: dict[str, dict[str, float]] = {}
    loop_consumed: dict[str, dict[str, float]] = {}
    loop_recovery: dict[str, dict[str, float]] = {}
    loop_purge: dict[str, dict[str, float]] = {}
    loop_metadata: dict[str, dict[str, object]] = {}
    loop_count = len(recycle_groups)
    separation_packet_index = {
        packet.unit_id: packet
        for packet in (separation_packets or [])
    }

    for source_unit_id, recycle_streams in recycle_groups.items():
        purge_streams = purge_groups.get(source_unit_id, [])
        if not purge_streams and loop_count == 1:
            purge_streams = [stream for group in purge_groups.values() for stream in group]
        recycle_targets = sorted({stream.destination_unit_id for stream in recycle_streams if stream.destination_unit_id})
        recycle_target_unit_id = recycle_targets[0] if len(recycle_targets) == 1 else None
        source_section_id = next((stream.section_id for stream in recycle_streams if stream.section_id), "")
        target_section_id = ""
        if recycle_target_unit_id:
            target_section_id = next(
                (stream.section_id for stream in streams if stream.destination_unit_id == recycle_target_unit_id and stream.section_id),
                "",
            )
        actual_recycle = _aggregate_component_molar(recycle_streams)
        actual_purge = _aggregate_component_molar(purge_streams)
        loop_id = f"{source_unit_id}_recycle_loop"
        structural_recycle_only = not purge_streams and source_unit_id in {"concentration", "primary_flash", "primary_separation"}
        component_names = sorted(set(recycle_solution) | set(actual_recycle) | set(actual_purge))
        loop_targets[loop_id] = {}
        loop_consumed[loop_id] = {}
        loop_recovery[loop_id] = {}
        loop_purge[loop_id] = {}
        loop_metadata[loop_id] = {
            "source_unit_id": source_unit_id,
            "target_unit_id": recycle_target_unit_id,
            "source_section_id": source_section_id,
            "target_section_id": target_section_id,
            "recycle_stream_ids": [stream.stream_id for stream in recycle_streams],
            "purge_stream_ids": [stream.stream_id for stream in purge_streams],
            "actual_recycle": actual_recycle,
            "actual_purge": actual_purge,
        }
        for component_name in component_names:
            share = _component_share(component_name, actual_recycle, total_recycle, actual_purge, total_purge, loop_count)
            global_total = float(recycle_solution.get(component_name, {}).get("total_flow", actual_recycle.get(component_name, 0.0) + actual_purge.get(component_name, 0.0)))
            global_recycle = float(recycle_solution.get(component_name, {}).get("recycle_flow", actual_recycle.get(component_name, 0.0)))
            global_purge = float(recycle_solution.get(component_name, {}).get("purge_flow", actual_purge.get(component_name, 0.0)))
            loop_target_total = max(global_total * share, actual_recycle.get(component_name, 0.0) + actual_purge.get(component_name, 0.0))
            loop_target_recycle = global_recycle * share
            loop_target_purge = global_purge * share
            actual_sum = actual_recycle.get(component_name, 0.0) + actual_purge.get(component_name, 0.0)
            if actual_sum > 1e-9:
                recovery_fraction = actual_recycle.get(component_name, 0.0) / actual_sum
                purge_fraction = actual_purge.get(component_name, 0.0) / actual_sum
            else:
                target_sum = loop_target_recycle + loop_target_purge
                recovery_fraction = loop_target_recycle / target_sum if target_sum > 1e-9 else 0.0
                purge_fraction = loop_target_purge / target_sum if target_sum > 1e-9 else 0.0
            impurity_family = _classify_impurity_family(component_name)
            min_purge = _recommended_min_purge_fraction(source_section_id, impurity_family)
            if structural_recycle_only:
                min_purge = 0.0
            packet = separation_packet_index.get(source_unit_id)
            direct_section_closure = False
            if packet is not None:
                packet_recycle = packet.component_split_to_recycle.get(component_name, 0.0)
                packet_waste = packet.component_split_to_waste.get(component_name, 0.0) + packet.component_split_to_side_draw.get(component_name, 0.0)
                packet_nonproduct = max(packet_recycle + packet_waste, 0.0)
                if packet_nonproduct > 1e-9:
                    section_recovery = packet_recycle / packet_nonproduct
                    section_purge = packet_waste / packet_nonproduct
                    direct_section_closure = _section_uses_direct_split_closure(source_section_id or source_unit_id) and packet.equilibrium_model != ""
                    if direct_section_closure:
                        loop_target_total = actual_sum if actual_sum > 1e-9 else max(loop_target_recycle + loop_target_purge, 0.0)
                        loop_target_recycle = loop_target_total * section_recovery
                        loop_target_purge = loop_target_total * section_purge
                        if section_recovery <= 1e-9:
                            recovery_fraction = 0.0
                            purge_fraction = 1.0
                        elif section_purge <= 1e-9:
                            recovery_fraction = 0.999999
                            purge_fraction = 0.0
                        else:
                            recovery_fraction = 1.0
                            purge_fraction = section_purge
                    else:
                        if packet.equilibrium_model:
                            recovery_fraction = max(recovery_fraction, section_recovery)
                            purge_fraction = max(purge_fraction, section_purge)
                        if packet.activity_model and "nrtl" in packet.activity_model:
                            purge_fraction = max(purge_fraction, min(section_purge + 0.02, 0.25))
            purge_fraction = max(purge_fraction, min_purge)
            if not direct_section_closure:
                recovery_fraction = min(recovery_fraction, max(1.0 - purge_fraction, 0.0))
            loop_targets[loop_id][component_name] = round(loop_target_total, 6)
            loop_consumed[loop_id][component_name] = round(max(loop_target_total - actual_sum, 0.0), 6)
            loop_recovery[loop_id][component_name] = round(max(0.0, min(recovery_fraction, 0.999999)), 6)
            loop_purge[loop_id][component_name] = round(max(0.0, min(purge_fraction, 0.999)), 6)

    loop_results = solve_multi_loop_recycle_network(loop_targets, loop_consumed, loop_recovery, loop_purge)

    packets: list[RecyclePacket] = []
    summaries: list[ConvergenceSummary] = []
    for loop_id, component_results in loop_results.items():
        metadata = loop_metadata[loop_id]
        actual_recycle = metadata["actual_recycle"]
        actual_purge = metadata["actual_purge"]
        component_targets = {name: round(float(result["total_flow"]), 6) for name, result in component_results.items()}
        component_fresh = {name: round(float(result["fresh_flow"]), 6) for name, result in component_results.items()}
        component_recycle = {name: round(float(result["recycle_flow"]), 6) for name, result in component_results.items()}
        component_purge = {name: round(float(result["purge_flow"]), 6) for name, result in component_results.items()}
        component_iterations = {name: int(result["iterations"]) for name, result in component_results.items()}
        component_errors: dict[str, float] = {}
        family_components: dict[str, list[str]] = defaultdict(list)
        family_recycle: dict[str, float] = defaultdict(float)
        family_purge: dict[str, float] = defaultdict(float)

        for component_name, result in component_results.items():
            recycle_target = component_recycle.get(component_name, 0.0)
            purge_target = component_purge.get(component_name, 0.0)
            recycle_error = abs(actual_recycle.get(component_name, 0.0) - recycle_target) / max(recycle_target, actual_recycle.get(component_name, 0.0), 1e-9) * 100.0
            target_recovery_ratio = recycle_target / max(recycle_target + purge_target, 1e-9)
            actual_recovery_ratio = actual_recycle.get(component_name, 0.0) / max(actual_recycle.get(component_name, 0.0) + actual_purge.get(component_name, 0.0), 1e-9)
            recovery_ratio_error = 0.0 if (not metadata["purge_stream_ids"] and metadata["source_unit_id"] in {"concentration", "primary_flash", "primary_separation"}) else abs(actual_recovery_ratio - target_recovery_ratio) * 100.0
            component_errors[component_name] = round(max(recycle_error, recovery_ratio_error), 6)

            family = _classify_impurity_family(component_name)
            family_components[family].append(component_name)
            family_recycle[family] += recycle_target
            family_purge[family] += purge_target

        purge_policy_by_family = {
            family: round(family_purge[family] / max(family_recycle[family] + family_purge[family], 1e-9), 6)
            for family in sorted(family_components)
        }
        max_iterations = max(component_iterations.values(), default=0)
        max_component_error = max(component_errors.values(), default=0.0)
        mean_component_error = (
            round(sum(component_errors.values()) / max(len(component_errors), 1), 6)
            if component_errors
            else 0.0
        )
        converged = all(bool(result["converged"]) for result in component_results.values())
        status = _status_from_error(max_component_error, overall_closure_error_pct, converged)
        converged_components = sorted([name for name, error in component_errors.items() if error <= 2.0])
        estimated_components = sorted([name for name, error in component_errors.items() if 2.0 < error <= 95.0])
        blocked_components = sorted([name for name, error in component_errors.items() if error > 95.0])
        notes: list[str] = []
        if not metadata["purge_stream_ids"]:
            notes.append("No explicit purge stream is present for this recycle loop; purge policy is structural and should be reviewed.")
            if metadata["source_unit_id"] in {"concentration", "primary_flash", "primary_separation"}:
                notes.append("Recycle-only closure was accepted for this BAC cleanup loop because no explicit purge stream exists at the solved section boundary.")
        if max_component_error > 10.0:
            notes.append(f"Loop max component error is {max_component_error:.3f}% and needs manual review.")
        if metadata["source_section_id"]:
            notes.append(
                f"Loop purge policy is biased by section topology: source section `{metadata['source_section_id']}` returning to `{metadata['target_unit_id'] or 'mixed targets'}`."
            )
        if metadata["target_unit_id"] is None:
            notes.append("Recycle loop fans into multiple target units; keep this loop at estimated status until routing is simplified.")
            status = "estimated" if status == "converged" else status

        summary_id = f"{loop_id}_summary"
        packets.append(
            RecyclePacket(
                packet_id=f"{loop_id}_packet",
                loop_id=loop_id,
                recycle_source_unit_id=metadata["source_unit_id"],
                recycle_target_unit_id=metadata["target_unit_id"],
                source_section_id=metadata["source_section_id"],
                target_section_id=metadata["target_section_id"],
                recycle_stream_ids=metadata["recycle_stream_ids"],
                purge_stream_ids=metadata["purge_stream_ids"],
                component_targets_kmol_hr=component_targets,
                component_fresh_kmol_hr=component_fresh,
                component_recycle_kmol_hr=component_recycle,
                component_purge_kmol_hr=component_purge,
                component_convergence_error_pct=component_errors,
                component_iterations=component_iterations,
                purge_policy_by_family=purge_policy_by_family,
                impurity_family_components={family: sorted(names) for family, names in family_components.items()},
                convergence_summary_id=summary_id,
                convergence_status=status,
                closure_error_pct=round(overall_closure_error_pct, 6),
                max_iterations=max_iterations,
                notes=notes,
                citations=citations,
                assumptions=assumptions,
            )
        )
        summaries.append(
            ConvergenceSummary(
                summary_id=summary_id,
                loop_id=loop_id,
                recycle_source_unit_id=metadata["source_unit_id"],
                recycle_target_unit_id=metadata["target_unit_id"],
                source_section_id=metadata["source_section_id"],
                target_section_id=metadata["target_section_id"],
                recycle_stream_ids=metadata["recycle_stream_ids"],
                purge_stream_ids=metadata["purge_stream_ids"],
                component_count=len(component_errors),
                converged_components=converged_components,
                estimated_components=estimated_components,
                blocked_components=blocked_components,
                max_component_error_pct=max_component_error,
                mean_component_error_pct=mean_component_error,
                max_iterations=max_iterations,
                purge_policy_by_family=purge_policy_by_family,
                impurity_family_components={family: sorted(names) for family, names in family_components.items()},
                convergence_status=status,
                notes=notes,
                citations=citations,
                assumptions=assumptions,
            )
        )
    return packets, summaries
