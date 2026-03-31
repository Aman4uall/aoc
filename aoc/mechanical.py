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


def _support_type(equipment_type: str, service: str = "") -> str:
    lowered = f"{equipment_type} {service}".lower()
    if "header" in lowered:
        return "pipe rack support"
    if "htm circulation" in lowered:
        return "base frame"
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


def _nozzle_diameter_mm(volume_m3: float, duty_kw: float, equipment_type: str, service: str = "") -> float:
    lowered = f"{equipment_type} {service}".lower()
    if "control" in lowered:
        return 25.0
    if "header" in lowered:
        return max(85.0 + math.sqrt(max(duty_kw, 1.0)) * 1.8, 85.0)
    if "pump" in lowered:
        return max(40.0 + math.sqrt(max(duty_kw, 1.0)) * 1.2, 40.0)
    if "reboiler" in lowered or "condenser" in lowered:
        return max(65.0 + math.sqrt(max(duty_kw, 1.0)) * 2.0, 65.0)
    base = 80.0 + math.sqrt(max(volume_m3, 0.1)) * 55.0 + math.sqrt(max(duty_kw, 1.0)) * 2.5
    if "column" in lowered or "absorber" in lowered:
        base *= 1.35
    return max(base, 50.0)


def _operating_load_kn(volume_m3: float, duty_kw: float, equipment_type: str, service: str = "", design_pressure_bar: float = 0.0) -> float:
    lowered = f"{equipment_type} {service}".lower()
    if "pump" in lowered:
        return max(18.0 + duty_kw * 0.018, 18.0)
    if "control" in lowered:
        return 6.0
    if "header" in lowered:
        return max(24.0 + duty_kw * 0.016 + max(design_pressure_bar, 1.0) * 1.8, 24.0)
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


def _nozzle_reinforcement_area_mm2(nozzle_diameter_mm: float, design_pressure_bar: float, equipment_type: str, service: str = "") -> float:
    lowered = f"{equipment_type} {service}".lower()
    multiplier = 1.3 if any(token in lowered for token in ("reboiler", "condenser", "reactor", "column")) else 0.7
    if "header" in lowered or "htm" in lowered:
        multiplier += 0.25
    return max(nozzle_diameter_mm * max(design_pressure_bar, 1.0) * multiplier * 8.0, 250.0)


def _pressure_class(design_pressure_bar: float) -> str:
    if design_pressure_bar >= 20.0:
        return "ASME 600"
    if design_pressure_bar >= 10.0:
        return "ASME 300"
    if design_pressure_bar >= 5.0:
        return "ASME 150"
    return "PN16"


def _support_load_case(equipment_type: str, service: str = "") -> str:
    lowered = f"{equipment_type} {service}".lower()
    if "header" in lowered:
        return "rack piping + thermal expansion"
    if "column" in lowered or "absorber" in lowered or "reactor" in lowered:
        return "operating + wind + seismic + nozzle loads"
    if "tank" in lowered or "expansion" in lowered:
        return "operating + settlement + thermal growth"
    if "pump" in lowered or "control" in lowered:
        return "skid dead load + piping reaction"
    return "operating + nozzle loads"


def _wind_load_kn(reference_length_m: float, diameter_m: float, equipment_type: str, service: str = "") -> float:
    lowered = f"{equipment_type} {service}".lower()
    area_proxy = max(reference_length_m * diameter_m, 0.8)
    factor = 0.55
    if "column" in lowered or "absorber" in lowered or "reactor" in lowered:
        factor = 1.20
    elif "header" in lowered:
        factor = 0.85
    elif "tank" in lowered:
        factor = 0.70
    return max(area_proxy * factor, 1.5)


def _seismic_load_kn(operating_load_kn: float, equipment_type: str, service: str = "") -> float:
    lowered = f"{equipment_type} {service}".lower()
    fraction = 0.10
    if "column" in lowered or "absorber" in lowered or "reactor" in lowered:
        fraction = 0.18
    elif "header" in lowered:
        fraction = 0.12
    elif "pump" in lowered:
        fraction = 0.08
    return max(operating_load_kn * fraction, 1.0)


def _piping_load_kn(nozzle_diameter_mm: float, equipment_type: str, service: str = "", design_pressure_bar: float = 0.0) -> float:
    lowered = f"{equipment_type} {service}".lower()
    base = nozzle_diameter_mm * 0.025 + max(design_pressure_bar, 1.0) * 0.35
    if "header" in lowered or "htm" in lowered:
        base *= 1.45
    elif "reboiler" in lowered or "condenser" in lowered:
        base *= 1.20
    return max(base, 2.0)


def _platform_requirements(equipment_type: str, service: str = "", reference_length_m: float = 0.0) -> tuple[bool, float]:
    lowered = f"{equipment_type} {service}".lower()
    if "column" in lowered or "absorber" in lowered or "reactor" in lowered:
        area = max(reference_length_m * 1.15, 4.5)
        return True, round(area, 3)
    if "reboiler" in lowered or "condenser" in lowered or "exchanger" in lowered:
        return True, 3.0
    return False, 0.0


def _foundation_note(support_type: str, pipe_rack_tie_in_required: bool, maintenance_platform_required: bool) -> str:
    if pipe_rack_tie_in_required:
        return "Utility-header service assumes pipe-rack tie-in with local guide/restraint design."
    if "skirt" in support_type.lower():
        return "Tall vessel service assumes ring foundation and local anchor-chair reinforcement."
    if maintenance_platform_required:
        return "Access platform and ladder loads are included in the support screening basis."
    return "Base/foundation detail remains a preliminary screening basis."


def _support_variant(support_type: str, equipment_type: str, service: str = "") -> str:
    lowered = f"{support_type} {equipment_type} {service}".lower()
    if "pipe rack" in lowered:
        return "guided rack shoe"
    if "skirt" in lowered:
        return "cylindrical skirt with anchor chair"
    if "saddle" in lowered:
        return "dual saddle"
    if "leg" in lowered:
        return "four-leg support"
    if "instrument" in lowered:
        return "panel frame"
    return "grouted base frame"


def _anchor_group_count(support_type: str, equipment_type: str, service: str = "") -> int:
    lowered = f"{support_type} {equipment_type} {service}".lower()
    if "pipe rack" in lowered:
        return 2
    if "skirt" in lowered:
        return 8
    if "saddle" in lowered:
        return 6
    if "leg" in lowered:
        return 4
    if "instrument" in lowered:
        return 4
    return 4


def _foundation_footprint_m2(
    support_type: str,
    diameter_m: float,
    reference_length_m: float,
    platform_area_m2: float,
    equipment_type: str,
) -> float:
    lowered = f"{support_type} {equipment_type}".lower()
    if "pipe rack" in lowered:
        return round(max(reference_length_m * 0.9, 1.8), 3)
    if "skirt" in lowered:
        return round(max(math.pi * (diameter_m * 0.8) ** 2, 3.5) + 0.20 * platform_area_m2, 3)
    if "saddle" in lowered:
        return round(max(reference_length_m * diameter_m * 0.55, 2.8), 3)
    if "leg" in lowered:
        return round(max(diameter_m * diameter_m * 0.9, 1.6), 3)
    return round(max(diameter_m * 1.2, 1.2), 3)


def _maintenance_clearance_m(equipment_type: str, service: str = "", support_type: str = "") -> float:
    lowered = f"{equipment_type} {service} {support_type}".lower()
    if "column" in lowered or "absorber" in lowered or "reactor" in lowered:
        return 1.8
    if "header" in lowered:
        return 1.2
    if "pump" in lowered or "control" in lowered:
        return 1.0
    if "exchanger" in lowered or "reboiler" in lowered or "condenser" in lowered:
        return 1.5
    return 1.2


def _access_ladder_required(equipment_type: str, service: str = "", reference_length_m: float = 0.0) -> bool:
    lowered = f"{equipment_type} {service}".lower()
    return (
        "column" in lowered
        or "absorber" in lowered
        or "reactor" in lowered
        or reference_length_m >= 4.5
    )


def _lifting_lug_required(equipment_type: str, volume_m3: float, duty_kw: float) -> bool:
    lowered = equipment_type.lower()
    return (
        "exchanger" in lowered
        or "reboiler" in lowered
        or "condenser" in lowered
        or volume_m3 >= 8.0
        or duty_kw >= 120.0
    )


def _nozzle_services(equipment_type: str, service: str = "") -> list[str]:
    lowered = f"{equipment_type} {service}".lower()
    if "header" in lowered:
        return ["inlet", "outlet", "branch", "drain"]
    if "column" in lowered or "absorber" in lowered:
        return ["feed", "overhead", "bottoms", "instrument"]
    if "reactor" in lowered:
        return ["feed", "product", "utility", "instrument"]
    if "tank" in lowered:
        return ["inlet", "outlet", "vent"]
    return ["inlet", "outlet", "instrument"]


def _nozzle_orientations(nozzle_count: int, equipment_type: str, service: str = "") -> list[float]:
    lowered = f"{equipment_type} {service}".lower()
    if "column" in lowered or "absorber" in lowered or "reactor" in lowered:
        base = [0.0, 90.0, 180.0, 270.0]
    else:
        base = [0.0, 180.0, 270.0]
    return base[:nozzle_count]


def _nozzle_reinforcement_family(equipment_type: str, service: str = "", design_pressure_bar: float = 0.0) -> str:
    lowered = f"{equipment_type} {service}".lower()
    if "header" in lowered or "htm" in lowered:
        return "set-on repad"
    if "column" in lowered or "absorber" in lowered or "reactor" in lowered:
        return "integral repad"
    if design_pressure_bar >= 12.0:
        return "set-in reinforcement"
    return "shell excess area"


def _local_shell_load_interaction_factor(
    nozzle_diameter_mm: float,
    diameter_m: float,
    design_pressure_bar: float,
    equipment_type: str,
    service: str = "",
) -> float:
    lowered = f"{equipment_type} {service}".lower()
    ratio = nozzle_diameter_mm / max(diameter_m * 1000.0, 1.0)
    base = 1.0 + ratio * 1.8 + max(design_pressure_bar, 1.0) * 0.015
    if "column" in lowered or "absorber" in lowered or "reactor" in lowered:
        base += 0.12
    if "header" in lowered:
        base += 0.08
    return round(max(base, 1.0), 3)


def _nozzle_projection_mm(nozzle_diameter_mm: float, equipment_type: str, service: str = "") -> float:
    lowered = f"{equipment_type} {service}".lower()
    multiplier = 1.25 if ("header" in lowered or "htm" in lowered) else 1.05
    return round(max(nozzle_diameter_mm * multiplier, 90.0), 3)


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
        nozzle_diameter_mm = _nozzle_diameter_mm(spec.volume_m3, spec.duty_kw, spec.equipment_type, spec.service)
        operating_load_kn = _operating_load_kn(spec.volume_m3, spec.duty_kw, spec.equipment_type, spec.service, spec.design_pressure_bar)
        thermal_growth_mm = _thermal_growth_mm(spec.design_temperature_c, reference_length_m, spec.material_of_construction)
        reinforcement_area_mm2 = _nozzle_reinforcement_area_mm2(nozzle_diameter_mm, spec.design_pressure_bar, spec.equipment_type, spec.service)
        support_type = _support_type(spec.equipment_type, spec.service)
        support_load_case = _support_load_case(spec.equipment_type, spec.service)
        pressure_class = _pressure_class(spec.design_pressure_bar)
        hydrotest_pressure_bar = max(spec.design_pressure_bar * 1.30, spec.design_pressure_bar + 1.0)
        design_vertical_load_kn = max(operating_load_kn * 1.08, operating_load_kn + 1.0)
        piping_load_kn = _piping_load_kn(nozzle_diameter_mm, spec.equipment_type, spec.service, spec.design_pressure_bar)
        wind_load_kn = _wind_load_kn(reference_length_m, diameter_m, spec.equipment_type, spec.service)
        seismic_load_kn = _seismic_load_kn(operating_load_kn, spec.equipment_type, spec.service)
        maintenance_platform_required, platform_area_m2 = _platform_requirements(spec.equipment_type, spec.service, reference_length_m)
        pipe_rack_tie_in_required = "header" in f"{spec.equipment_type} {spec.service}".lower()
        support_variant = _support_variant(support_type, spec.equipment_type, spec.service)
        anchor_group_count = _anchor_group_count(support_type, spec.equipment_type, spec.service)
        foundation_footprint_m2 = _foundation_footprint_m2(
            support_type,
            diameter_m,
            reference_length_m,
            platform_area_m2,
            spec.equipment_type,
        )
        maintenance_clearance_m = _maintenance_clearance_m(spec.equipment_type, spec.service, support_type)
        access_ladder_required = _access_ladder_required(spec.equipment_type, spec.service, reference_length_m)
        lifting_lug_required = _lifting_lug_required(spec.equipment_type, spec.volume_m3, spec.duty_kw)
        nozzle_reinforcement_family = _nozzle_reinforcement_family(spec.equipment_type, spec.service, spec.design_pressure_bar)
        local_shell_load_interaction_factor = _local_shell_load_interaction_factor(
            nozzle_diameter_mm,
            diameter_m,
            spec.design_pressure_bar,
            spec.equipment_type,
            spec.service,
        )
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
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_connection_class",
                    title="Connection class",
                    formula="Class = f(design pressure)",
                    substitutions={"P": f"{spec.design_pressure_bar:.2f} bar"},
                    result=pressure_class,
                    units="class",
                ),
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_foundation_basis",
                    title="Foundation / access basis",
                    formula="Footprint = f(support family, diameter, access area)",
                    substitutions={
                        "support_variant": support_variant,
                        "platform_area": f"{platform_area_m2:.3f} m2",
                    },
                    result=f"{foundation_footprint_m2:.3f}",
                    units="m2",
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
                    formula="W_support = vertical + piping + wind + seismic screening loads",
                    substitutions={
                        "vertical": f"{design_vertical_load_kn:.3f} kN",
                        "piping": f"{piping_load_kn:.3f} kN",
                        "wind": f"{wind_load_kn:.3f} kN",
                        "seismic": f"{seismic_load_kn:.3f} kN",
                    },
                    result=f"{max(design_vertical_load_kn + piping_load_kn + wind_load_kn + seismic_load_kn, operating_load_kn):.3f}",
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
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_local_shell_interaction",
                    title="Local shell / nozzle interaction",
                    formula="Interaction = f(nozzle-to-shell ratio, pressure, equipment family)",
                    substitutions={
                        "reinforcement_family": nozzle_reinforcement_family,
                        "d_nozzle": f"{nozzle_diameter_mm:.1f} mm",
                        "D_shell": f"{diameter_m:.3f} m",
                    },
                    result=f"{local_shell_load_interaction_factor:.3f}",
                    units="factor",
                ),
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_hydrotest",
                    title="Hydrotest pressure",
                    formula="P_hydro = max(1.3*P_design, P_design + 1 bar)",
                    substitutions={"P_design": f"{spec.design_pressure_bar:.2f} bar"},
                    result=f"{hydrotest_pressure_bar:.3f}",
                    units="bar",
                ),
                CalcTrace(
                    trace_id=f"{spec.equipment_id}_foundation_basis",
                    title="Foundation / access basis",
                    formula="Footprint = f(support family, diameter, access area)",
                    substitutions={
                        "support_variant": support_variant,
                        "platform_area": f"{platform_area_m2:.3f} m2",
                        "clearance": f"{maintenance_clearance_m:.2f} m",
                    },
                    result=f"{foundation_footprint_m2:.3f}",
                    units="m2",
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
                allowable_stress_mpa=round(allowable_stress, 3),
                joint_efficiency=round(joint_efficiency, 3),
                corrosion_allowance_mm=round(corrosion_allowance, 3),
                shell_thickness_mm=round(shell_thickness_mm, 3),
                head_thickness_mm=round(head_thickness_mm, 3),
                nozzle_diameter_mm=round(nozzle_diameter_mm, 3),
                support_type=support_type,
                support_variant=support_variant,
                support_thickness_mm=round(support_thickness_mm, 3),
                operating_load_kn=round(operating_load_kn, 3),
                thermal_growth_mm=round(thermal_growth_mm, 3),
                nozzle_reinforcement_area_mm2=round(reinforcement_area_mm2, 3),
                support_load_case=support_load_case,
                pressure_class=pressure_class,
                hydrotest_pressure_bar=round(hydrotest_pressure_bar, 3),
                design_vertical_load_kn=round(design_vertical_load_kn, 3),
                piping_load_kn=round(piping_load_kn, 3),
                wind_load_kn=round(wind_load_kn, 3),
                seismic_load_kn=round(seismic_load_kn, 3),
                maintenance_platform_required=maintenance_platform_required,
                platform_area_m2=round(platform_area_m2, 3),
                pipe_rack_tie_in_required=pipe_rack_tie_in_required,
                anchor_group_count=anchor_group_count,
                foundation_footprint_m2=round(foundation_footprint_m2, 3),
                maintenance_clearance_m=round(maintenance_clearance_m, 3),
                access_ladder_required=access_ladder_required,
                lifting_lug_required=lifting_lug_required,
                nozzle_reinforcement_family=nozzle_reinforcement_family,
                local_shell_load_interaction_factor=local_shell_load_interaction_factor,
                notes=(
                    f"Preliminary mechanical basis for {spec.service}; class {pressure_class}; "
                    f"load case {support_load_case}; support variant {support_variant}; "
                    f"reinforcement family {nozzle_reinforcement_family}."
                ),
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
        "| Equipment | Type | Shell t (mm) | Head t (mm) | Class | Hydrotest (bar) | Nozzle (mm) | Support | Load Case | Support t (mm) | Load (kN) | Thermal Growth (mm) | Reinforcement (mm2) | Platform |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        rows.append(
            f"| {item.equipment_id} | {item.equipment_type} | {item.shell_thickness_mm:.2f} | {item.head_thickness_mm:.2f} | {item.pressure_class} | {item.hydrotest_pressure_bar:.2f} | {item.nozzle_diameter_mm:.1f} | {item.support_type} | {item.support_load_case} | {item.support_thickness_mm:.2f} | {item.operating_load_kn:.2f} | {item.thermal_growth_mm:.2f} | {item.nozzle_reinforcement_area_mm2:.1f} | {'yes' if item.maintenance_platform_required else 'no'} |"
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
        support_design_basis="Support screening includes vertical, piping, wind, seismic, and thermal-growth load components by equipment family.",
        load_case_basis="Tall process equipment uses operating + wind + seismic + nozzle loads; headers use rack piping + thermal expansion; skids use dead load + piping reaction.",
        connection_rating_basis="Nozzle and header connection classes follow design-pressure screening via ASME/PN envelope mapping.",
        access_platform_basis="Columns, absorbers, reactors, and exchanger services above grade include screening access-platform area allowances.",
        foundation_basis="Support variants differentiate skirt, saddle, leg, rack, and skid foundations with screening footprint and anchor-group logic.",
        nozzle_load_basis="Nozzle schedules include reinforcement family, local shell interaction, orientation, projection, and screening piping load allocation.",
        markdown="Mechanical basis uses ASME-style screening equations for shell, head, nozzle, support, load-case, and connection-class sizing.",
        citations=mechanical_design.citations,
        assumptions=mechanical_design.assumptions,
    )


def build_vessel_mechanical_designs(mechanical_design: MechanicalDesignArtifact) -> list[VesselMechanicalDesign]:
    vessel_designs: list[VesselMechanicalDesign] = []
    for item in mechanical_design.items:
        support_load_basis_kn = max(
            item.design_vertical_load_kn + item.piping_load_kn + item.wind_load_kn + item.seismic_load_kn,
            item.operating_load_kn * 1.15,
            item.support_thickness_mm * 3.8,
            12.0,
        )
        foundation_note = _foundation_note(
            item.support_type,
            item.pipe_rack_tie_in_required,
            item.maintenance_platform_required,
        )
        support = SupportDesign(
            equipment_id=item.equipment_id,
            support_type=item.support_type,
            support_variant=item.support_variant,
            support_load_basis_kn=round(support_load_basis_kn, 3),
            support_load_case=item.support_load_case,
            support_thickness_mm=item.support_thickness_mm,
            operating_load_kn=item.operating_load_kn,
            design_vertical_load_kn=item.design_vertical_load_kn,
            piping_load_kn=item.piping_load_kn,
            wind_load_kn=item.wind_load_kn,
            seismic_load_kn=item.seismic_load_kn,
            overturning_moment_kn_m=round(max(item.operating_load_kn * 0.65, 5.0), 3),
            thermal_growth_mm=item.thermal_growth_mm,
            anchor_bolt_diameter_mm=round(max(item.nozzle_diameter_mm * 0.22 + support_load_basis_kn * 0.025, 20.0), 3),
            base_plate_thickness_mm=round(max(item.support_thickness_mm * 0.85 + item.wind_load_kn * 0.08, 18.0), 3),
            maintenance_platform_required=item.maintenance_platform_required,
            platform_area_m2=item.platform_area_m2,
            pipe_rack_tie_in_required=item.pipe_rack_tie_in_required,
            anchor_group_count=item.anchor_group_count,
            foundation_footprint_m2=item.foundation_footprint_m2,
            maintenance_clearance_m=item.maintenance_clearance_m,
            access_ladder_required=item.access_ladder_required,
            lifting_lug_required=item.lifting_lug_required,
            foundation_note=foundation_note,
            markdown=(
                f"{item.equipment_id} uses {item.support_variant} ({item.support_type}) with load case '{item.support_load_case}', "
                f"vertical/piping/wind/seismic loads of {item.design_vertical_load_kn:.3f}/{item.piping_load_kn:.3f}/{item.wind_load_kn:.3f}/{item.seismic_load_kn:.3f} kN, "
                f"thermal growth {item.thermal_growth_mm:.3f} mm, and screening anchor-bolt/base-plate sizing."
            ),
            citations=item.citations,
            assumptions=item.assumptions,
        )
        nozzle_services = _nozzle_services(item.equipment_type)
        nozzle_count = len(nozzle_services)
        nozzle_orientations = _nozzle_orientations(nozzle_count, item.equipment_type)
        nozzle_schedule = NozzleSchedule(
            equipment_id=item.equipment_id,
            nozzle_count=nozzle_count,
            nozzle_diameters_mm=[item.nozzle_diameter_mm] * nozzle_count,
            nozzle_services=nozzle_services,
            reinforcement_area_mm2=[item.nozzle_reinforcement_area_mm2] * nozzle_count,
            nozzle_pressure_class=_pressure_class(item.design_pressure_bar),
            nozzle_orientations_deg=nozzle_orientations,
            nozzle_connection_classes=[item.pressure_class] * nozzle_count,
            nozzle_load_cases_kn=[round(max(item.piping_load_kn / max(nozzle_count, 1), 0.8), 3)] * nozzle_count,
            nozzle_reinforcement_family=item.nozzle_reinforcement_family,
            nozzle_projection_mm=[_nozzle_projection_mm(item.nozzle_diameter_mm, item.equipment_type)] * nozzle_count,
            local_shell_load_factors=[item.local_shell_load_interaction_factor] * nozzle_count,
            markdown=(
                f"Nozzle schedule for {item.equipment_id} derived from screening nozzle diameter {item.nozzle_diameter_mm:.1f} mm "
                f"with reinforcement area {item.nozzle_reinforcement_area_mm2:.1f} mm2, reinforcement family {item.nozzle_reinforcement_family}, "
                f"and class {_pressure_class(item.design_pressure_bar)}."
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
                hydrotest_pressure_bar=item.hydrotest_pressure_bar,
                pressure_class=item.pressure_class,
                access_platform_required=item.maintenance_platform_required,
                support_variant=item.support_variant,
                anchor_group_count=item.anchor_group_count,
                foundation_footprint_m2=item.foundation_footprint_m2,
                support_design=support,
                nozzle_schedule=nozzle_schedule,
                markdown=f"Preliminary vessel mechanical design generated for {item.equipment_id} with class {item.pressure_class} and hydrotest {item.hydrotest_pressure_bar:.2f} bar.",
                citations=item.citations,
                assumptions=item.assumptions,
            )
        )
    return vessel_designs
