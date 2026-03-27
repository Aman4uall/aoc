from __future__ import annotations

import math

from aoc.models import (
    CalcTrace,
    EquipmentListArtifact,
    MechanicalDesignBasis,
    MechanicalComponentDesign,
    MechanicalDesignArtifact,
    NozzleSchedule,
    SensitivityLevel,
    SupportDesign,
    VesselMechanicalDesign,
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
    if "pump" in lowered:
        return "base frame"
    if "control" in lowered:
        return "instrument frame"
    if "reboiler" in lowered or "condenser" in lowered or "exchanger" in lowered:
        return "saddle support"
    if "expansion" in lowered:
        return "leg support"
    if "relief" in lowered:
        return "base support"
    if "column" in lowered or "absorber" in lowered:
        return "skirt support"
    if "tank" in lowered:
        return "saddle / leg support"
    if "reactor" in lowered:
        return "skirt support"
    return "base support"


def _nozzle_diameter_mm(volume_m3: float, duty_kw: float, equipment_type: str) -> float:
    lowered = equipment_type.lower()
    if "control" in lowered:
        return 25.0
    if "pump" in lowered:
        return max(40.0 + math.sqrt(max(duty_kw, 1.0)) * 1.2, 40.0)
    if "reboiler" in lowered or "condenser" in lowered:
        return max(65.0 + math.sqrt(max(duty_kw, 1.0)) * 2.0, 65.0)
    base = 80.0 + math.sqrt(max(volume_m3, 0.1)) * 55.0 + math.sqrt(max(duty_kw, 1.0)) * 2.5
    if "column" in lowered or "absorber" in lowered:
        base *= 1.35
    return max(base, 50.0)


def _operating_load_kn(volume_m3: float, duty_kw: float, equipment_type: str) -> float:
    lowered = equipment_type.lower()
    if "pump" in lowered:
        return max(18.0 + duty_kw * 0.018, 18.0)
    if "control" in lowered:
        return 6.0
    density_proxy = 980.0
    if "expansion" in lowered or "storage" in lowered:
        density_proxy = 900.0
    if "relief" in lowered:
        density_proxy = 850.0
    static_load = volume_m3 * density_proxy * 9.81 / 1000.0
    thermal_allowance = duty_kw * 0.012
    return max(static_load + thermal_allowance + 8.0, 10.0)


def _thermal_growth_mm(design_temperature_c: float, reference_length_m: float, equipment_type: str) -> float:
    lowered = equipment_type.lower()
    alpha = 17e-6 if "316" in lowered or "304" in lowered else 12e-6
    delta_t = max(design_temperature_c - 25.0, 5.0)
    return alpha * delta_t * max(reference_length_m, 1.0) * 1000.0


def _nozzle_reinforcement_area_mm2(nozzle_diameter_mm: float, design_pressure_bar: float, equipment_type: str) -> float:
    multiplier = 1.3 if any(token in equipment_type.lower() for token in ("reboiler", "condenser", "reactor", "column")) else 0.7
    return max(nozzle_diameter_mm * max(design_pressure_bar, 1.0) * multiplier * 8.0, 250.0)


def _pressure_class(design_pressure_bar: float) -> str:
    if design_pressure_bar >= 20.0:
        return "ASME 600"
    if design_pressure_bar >= 10.0:
        return "ASME 300"
    if design_pressure_bar >= 5.0:
        return "ASME 150"
    return "PN16"


def build_mechanical_design_artifact(equipment: EquipmentListArtifact) -> MechanicalDesignArtifact:
    items: list[MechanicalComponentDesign] = []
    for spec in equipment.items:
        lowered_type = spec.equipment_type.lower()
        allowable_stress = _allowable_stress_mpa(spec.material_of_construction)
        corrosion_allowance = _corrosion_allowance_mm(spec.material_of_construction, spec.service)
        joint_efficiency = 0.85
        diameter_m = max((4.0 * max(spec.volume_m3, 0.5) / (math.pi * 6.0)) ** (1.0 / 3.0), 0.9)
        reference_length_m = max(diameter_m * 3.0, 1.2)
        pressure_mpa = max(spec.design_pressure_bar / 10.0, 0.05)
        if "pump" in lowered_type or "control" in lowered_type:
            shell_thickness_mm = 0.0
            head_thickness_mm = 0.0
        else:
            shell_thickness_mm = ((pressure_mpa * diameter_m * 1000.0) / max((2.0 * allowable_stress * joint_efficiency - 1.2 * pressure_mpa), 1.0)) + corrosion_allowance
            head_thickness_mm = shell_thickness_mm * 0.92
        nozzle_diameter_mm = _nozzle_diameter_mm(spec.volume_m3, spec.duty_kw, spec.equipment_type)
        operating_load_kn = _operating_load_kn(spec.volume_m3, spec.duty_kw, spec.equipment_type)
        thermal_growth_mm = _thermal_growth_mm(spec.design_temperature_c, reference_length_m, spec.material_of_construction)
        reinforcement_area_mm2 = _nozzle_reinforcement_area_mm2(nozzle_diameter_mm, spec.design_pressure_bar, spec.equipment_type)
        support_type = _support_type(spec.equipment_type)
        support_thickness_mm = max(shell_thickness_mm * 0.70, 12.0 if "pump" in lowered_type or "control" in lowered_type else 18.0 if "tank" in lowered_type else 24.0)
        if "pump" in lowered_type or "control" in lowered_type:
            traces = [
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_support_basis",
                    title="Skid or frame support basis",
                    formula="t_support = max(screening minimum, service family basis)",
                    substitutions={"service_family": spec.equipment_type},
                    result=f"{support_thickness_mm:.3f}",
                    units="mm",
                ),
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_connection",
                    title="Connection basis",
                    formula="d_conn = f(duty, service family)",
                    substitutions={"duty": f"{spec.duty_kw:.3f} kW"},
                    result=f"{nozzle_diameter_mm:.1f}",
                    units="mm",
                ),
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_support_load",
                    title="Support load basis",
                    formula="W = static load proxy + thermal allowance",
                    substitutions={"volume": f"{spec.volume_m3:.3f} m3", "duty": f"{spec.duty_kw:.3f} kW"},
                    result=f"{operating_load_kn:.3f}",
                    units="kN",
                ),
            ]
        else:
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
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_support_load",
                    title="Support load basis",
                    formula="W = static load proxy + thermal allowance",
                    substitutions={"volume": f"{spec.volume_m3:.3f} m3", "duty": f"{spec.duty_kw:.3f} kW"},
                    result=f"{operating_load_kn:.3f}",
                    units="kN",
                ),
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_thermal_growth",
                    title="Thermal growth",
                    formula="delta = alpha * L * dT",
                    substitutions={"L": f"{reference_length_m:.3f} m", "dT": f"{max(spec.design_temperature_c - 25.0, 5.0):.1f} C"},
                    result=f"{thermal_growth_mm:.3f}",
                    units="mm",
                ),
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_nozzle_reinforcement",
                    title="Nozzle reinforcement area",
                    formula="A = f(d_nozzle, design pressure, equipment family)",
                    substitutions={"d_nozzle": f"{nozzle_diameter_mm:.1f} mm", "P": f"{spec.design_pressure_bar:.2f} bar"},
                    result=f"{reinforcement_area_mm2:.3f}",
                    units="mm2",
                ),
            ]
        assumptions = spec.assumptions + [
            "Mechanical calculations remain feasibility-study level and are not a substitute for code-stamped detailed design.",
        ]
        if "pump" in lowered_type or "control" in lowered_type:
            assumptions.append("Rotating and control-package items use support-frame screening rather than vessel shell-thickness equations.")
        else:
            assumptions.append("Shell thickness uses allowable-stress and joint-efficiency screening logic with corrosion allowance.")
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
                operating_load_kn=round(operating_load_kn, 3),
                thermal_growth_mm=round(thermal_growth_mm, 3),
                nozzle_reinforcement_area_mm2=round(reinforcement_area_mm2, 3),
                notes=f"Preliminary mechanical basis for {spec.service}.",
                calc_traces=traces,
                value_records=[
                    make_value_record(f"{spec.equipment_id}_shell_thickness", f"{spec.equipment_id} shell thickness", shell_thickness_mm, "mm", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
                    make_value_record(f"{spec.equipment_id}_nozzle_diameter", f"{spec.equipment_id} nozzle diameter", nozzle_diameter_mm, "mm", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
                    make_value_record(f"{spec.equipment_id}_support_load", f"{spec.equipment_id} support load basis", operating_load_kn, "kN", citations=citations, assumptions=assumptions, sensitivity=SensitivityLevel.MEDIUM),
                ],
                citations=citations,
                assumptions=assumptions,
            )
        )

    rows = [
        "| Equipment | Type | Shell t (mm) | Head t (mm) | Nozzle (mm) | Support | Support t (mm) | Load (kN) | Thermal Growth (mm) | Reinforcement (mm2) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        rows.append(
            f"| {item.equipment_id} | {item.equipment_type} | {item.shell_thickness_mm:.2f} | {item.head_thickness_mm:.2f} | {item.nozzle_diameter_mm:.1f} | {item.support_type} | {item.support_thickness_mm:.2f} | {item.operating_load_kn:.2f} | {item.thermal_growth_mm:.2f} | {item.nozzle_reinforcement_area_mm2:.1f} |"
        )
    return MechanicalDesignArtifact(
        items=items,
        markdown="\n".join(rows),
        value_records=[value for item in items for value in item.value_records],
        citations=sorted({citation for item in items for citation in item.citations}),
        assumptions=[assumption for item in items for assumption in item.assumptions],
    )


def build_mechanical_design_basis(mechanical_design: MechanicalDesignArtifact) -> MechanicalDesignBasis:
    return MechanicalDesignBasis(
        basis_id="mechanical_screening_basis",
        code_basis="ASME-style screening logic",
        design_pressure_basis="Selected equipment design pressure with feasibility-study margin",
        design_temperature_basis="Selected equipment design temperature with preliminary utility envelope",
        corrosion_allowance_mm=max((item.corrosion_allowance_mm for item in mechanical_design.items), default=3.0),
        markdown="Mechanical basis uses ASME-style screening equations for shell, head, nozzle, and support sizing.",
        citations=mechanical_design.citations,
        assumptions=mechanical_design.assumptions,
    )


def build_vessel_mechanical_designs(mechanical_design: MechanicalDesignArtifact) -> list[VesselMechanicalDesign]:
    vessel_designs: list[VesselMechanicalDesign] = []
    for item in mechanical_design.items:
        support = SupportDesign(
            equipment_id=item.equipment_id,
            support_type=item.support_type,
            support_load_basis_kn=round(max(item.operating_load_kn * 1.15, item.support_thickness_mm * 3.8, 12.0), 3),
            support_thickness_mm=item.support_thickness_mm,
            operating_load_kn=item.operating_load_kn,
            overturning_moment_kn_m=round(max(item.operating_load_kn * 0.65, 5.0), 3),
            thermal_growth_mm=item.thermal_growth_mm,
            anchor_bolt_diameter_mm=round(max(item.nozzle_diameter_mm * 0.22 + item.operating_load_kn * 0.04, 20.0), 3),
            base_plate_thickness_mm=round(max(item.support_thickness_mm * 0.85, 18.0), 3),
            markdown=(
                f"{item.equipment_id} uses {item.support_type} with operating load {item.operating_load_kn:.3f} kN, "
                f"thermal growth {item.thermal_growth_mm:.3f} mm, and screening anchor-bolt/base-plate sizing."
            ),
            citations=item.citations,
            assumptions=item.assumptions,
        )
        nozzle_schedule = NozzleSchedule(
            equipment_id=item.equipment_id,
            nozzle_count=4 if "column" in item.equipment_type.lower() else 3,
            nozzle_diameters_mm=[item.nozzle_diameter_mm] * (4 if "column" in item.equipment_type.lower() else 3),
            nozzle_services=["feed", "product", "vent", "instrument"][: (4 if "column" in item.equipment_type.lower() else 3)],
            reinforcement_area_mm2=[item.nozzle_reinforcement_area_mm2] * (4 if "column" in item.equipment_type.lower() else 3),
            nozzle_pressure_class=_pressure_class(item.design_pressure_bar),
            markdown=(
                f"Nozzle schedule for {item.equipment_id} derived from screening nozzle diameter {item.nozzle_diameter_mm:.1f} mm "
                f"with reinforcement area {item.nozzle_reinforcement_area_mm2:.1f} mm2 and class {_pressure_class(item.design_pressure_bar)}."
            ),
            citations=item.citations,
            assumptions=item.assumptions,
        )
        vessel_designs.append(
            VesselMechanicalDesign(
                equipment_id=item.equipment_id,
                shell_thickness_mm=item.shell_thickness_mm,
                head_thickness_mm=item.head_thickness_mm,
                corrosion_allowance_mm=item.corrosion_allowance_mm,
                support_design=support,
                nozzle_schedule=nozzle_schedule,
                markdown=f"Preliminary vessel mechanical design generated for {item.equipment_id}.",
                citations=item.citations,
                assumptions=item.assumptions,
            )
        )
    return vessel_designs
