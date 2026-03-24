from __future__ import annotations

import math

from aoc.models import (
    CalcTrace,
    EquipmentListArtifact,
    MechanicalComponentDesign,
    MechanicalDesignArtifact,
    SensitivityLevel,
)
from aoc.value_engine import make_value_record


def _allowable_stress_mpa(material: str) -> float:
    lowered = material.lower()
    if "316" in lowered or "304" in lowered:
        return 120.0
    if "alloy" in lowered:
        return 145.0
    if "rubber" in lowered:
        return 100.0
    return 138.0


def _corrosion_allowance_mm(material: str, service: str) -> float:
    lowered = f"{material} {service}".lower()
    if "acid" in lowered or "chlor" in lowered:
        return 4.5
    if "storage" in lowered:
        return 2.0
    return 3.0


def _support_type(equipment_type: str) -> str:
    lowered = equipment_type.lower()
    if "column" in lowered or "absorber" in lowered:
        return "skirt support"
    if "tank" in lowered:
        return "saddle / leg support"
    if "reactor" in lowered:
        return "skirt support"
    return "base support"


def _nozzle_diameter_mm(volume_m3: float, duty_kw: float, equipment_type: str) -> float:
    base = 80.0 + math.sqrt(max(volume_m3, 0.1)) * 55.0 + math.sqrt(max(duty_kw, 1.0)) * 2.5
    if "column" in equipment_type.lower() or "absorber" in equipment_type.lower():
        base *= 1.35
    return max(base, 50.0)


def build_mechanical_design_artifact(equipment: EquipmentListArtifact) -> MechanicalDesignArtifact:
    items: list[MechanicalComponentDesign] = []
    for spec in equipment.items:
        allowable_stress = _allowable_stress_mpa(spec.material_of_construction)
        corrosion_allowance = _corrosion_allowance_mm(spec.material_of_construction, spec.service)
        joint_efficiency = 0.85
        diameter_m = max((4.0 * max(spec.volume_m3, 0.5) / (math.pi * 6.0)) ** (1.0 / 3.0), 0.9)
        pressure_mpa = max(spec.design_pressure_bar / 10.0, 0.05)
        shell_thickness_mm = ((pressure_mpa * diameter_m * 1000.0) / max((2.0 * allowable_stress * joint_efficiency - 1.2 * pressure_mpa), 1.0)) + corrosion_allowance
        head_thickness_mm = shell_thickness_mm * 0.92
        nozzle_diameter_mm = _nozzle_diameter_mm(spec.volume_m3, spec.duty_kw, spec.equipment_type)
        support_type = _support_type(spec.equipment_type)
        support_thickness_mm = max(shell_thickness_mm * 0.70, 18.0 if "tank" in spec.equipment_type.lower() else 24.0)
        traces = [
            CalcTrace(
                trace_id=f"{spec.equipment_id}_shell_thickness",
                title="Shell thickness",
                formula="t = P*D / (2*S*J - 1.2*P) + CA",
                substitutions={
                    "P": f"{pressure_mpa:.3f} MPa",
                    "D": f"{diameter_m:.3f} m",
                    "S": f"{allowable_stress:.1f} MPa",
                    "J": f"{joint_efficiency:.2f}",
                    "CA": f"{corrosion_allowance:.1f} mm",
                },
                result=f"{shell_thickness_mm:.3f}",
                units="mm",
            ),
            CalcTrace(
                trace_id=f"{spec.equipment_id}_nozzle",
                title="Nozzle basis",
                formula="d_nozzle = f(volume, duty, equipment family)",
                substitutions={"volume": f"{spec.volume_m3:.3f} m3", "duty": f"{spec.duty_kw:.3f} kW"},
                result=f"{nozzle_diameter_mm:.1f}",
                units="mm",
            ),
        ]
        assumptions = spec.assumptions + [
            "Mechanical calculations remain feasibility-study level and are not a substitute for code-stamped detailed design.",
            "Shell thickness uses allowable-stress and joint-efficiency screening logic with corrosion allowance.",
        ]
        citations = spec.citations
        items.append(
            MechanicalComponentDesign(
                equipment_id=spec.equipment_id,
                equipment_type=spec.equipment_type,
                design_pressure_bar=spec.design_pressure_bar,
                design_temperature_c=spec.design_temperature_c,
                corrosion_allowance_mm=round(corrosion_allowance, 3),
                shell_thickness_mm=round(shell_thickness_mm, 3),
                head_thickness_mm=round(head_thickness_mm, 3),
                nozzle_diameter_mm=round(nozzle_diameter_mm, 3),
                support_type=support_type,
                support_thickness_mm=round(support_thickness_mm, 3),
                notes=f"Preliminary mechanical basis for {spec.service}.",
                calc_traces=traces,
                value_records=[
                    make_value_record(f"{spec.equipment_id}_shell_thickness", f"{spec.equipment_id} shell thickness", shell_thickness_mm, "mm", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
                    make_value_record(f"{spec.equipment_id}_nozzle_diameter", f"{spec.equipment_id} nozzle diameter", nozzle_diameter_mm, "mm", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
                ],
                citations=citations,
                assumptions=assumptions,
            )
        )

    rows = [
        "| Equipment | Type | Shell t (mm) | Head t (mm) | Nozzle (mm) | Support | Support t (mm) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        rows.append(
            f"| {item.equipment_id} | {item.equipment_type} | {item.shell_thickness_mm:.2f} | {item.head_thickness_mm:.2f} | {item.nozzle_diameter_mm:.1f} | {item.support_type} | {item.support_thickness_mm:.2f} |"
        )
    return MechanicalDesignArtifact(
        items=items,
        markdown="\n".join(rows),
        value_records=[value for item in items for value in item.value_records],
        citations=sorted({citation for item in items for citation in item.citations}),
        assumptions=[assumption for item in items for assumption in item.assumptions],
    )
