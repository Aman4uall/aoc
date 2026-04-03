from __future__ import annotations

import itertools
import re

from aoc.models import ProductProfileArtifact, ResearchBundle, RouteSurveyArtifact


_WHITESPACE_RE = re.compile(r"[^a-z0-9]+")
_NUMERIC_IDENTIFIER_RE = re.compile(r"^\s*(?:\d+(?:\.\d+)?%?|\d+(?:\.\d+)?\.)\s*$")
_PAGE_IDENTIFIER_RE = re.compile(r"^\s*\d+\s*(?:\|\s*)?p(?:\s*a){0,2}\s*g\s*e\b", re.IGNORECASE)
_PRESSURE_IDENTIFIER_RE = re.compile(r"^\s*\d+(?:\.\d+)?\s*(?:psig|psi|bar|kpa|mpa)\s*$", re.IGNORECASE)
_LEADING_NOISE_PHRASE_RE = re.compile(
    r"^\s*(?:and|of|as|use of|such as|make|forms?|power and|process|also involves|it involves|this process|that process)\b",
    re.IGNORECASE,
)
_IDENTIFIER_NOISE_TOKENS = {
    "page",
    "pages",
    "table",
    "figure",
    "fig",
    "process",
    "selected",
    "yield",
    "pressure",
    "temperature",
    "site",
    "raw",
    "material",
    "materials",
    "used",
    "use",
    "involves",
    "gets",
    "which",
    "this",
    "that",
    "the",
    "a",
    "an",
    "and",
    "of",
    "as",
    "such",
    "as",
    "is",
    "make",
    "form",
    "forms",
    "power",
    "boots",
    "hoechst",
    "celanese",
}


def normalize_chemical_name(name: str) -> str:
    return _WHITESPACE_RE.sub("_", name.strip().lower()).strip("_")


def is_valid_property_identifier_name(name: str) -> bool:
    stripped = name.strip()
    if not stripped:
        return False
    if _NUMERIC_IDENTIFIER_RE.match(stripped):
        return False
    if _PAGE_IDENTIFIER_RE.match(stripped):
        return False
    if _PRESSURE_IDENTIFIER_RE.match(stripped):
        return False
    if _LEADING_NOISE_PHRASE_RE.match(stripped):
        return False
    if sum(char.isalpha() for char in stripped) < 2:
        return False
    tokens = [token for token in re.split(r"[^a-z0-9]+", stripped.lower()) if token]
    if tokens and all(token in _IDENTIFIER_NOISE_TOKENS or token.isdigit() for token in tokens):
        return False
    if len(tokens) > 3 and any(token in _IDENTIFIER_NOISE_TOKENS for token in tokens):
        return False
    if any(token in {"page", "pages"} for token in tokens):
        return False
    if "%" in stripped and len(tokens) <= 2:
        return False
    return True


BENCHMARK_PROPERTY_LIBRARY: dict[str, dict[str, object]] = {
    "water": {
        "aliases": ["h2o"],
        "formula": "H2O",
        "cas_number": "7732-18-5",
        "properties": {
            "molecular_weight": (18.015, "g/mol"),
            "normal_boiling_point": (100.0, "C"),
            "melting_point": (0.0, "C"),
            "liquid_density": (997.0, "kg/m3"),
            "liquid_viscosity": (0.00089, "Pa.s"),
            "liquid_heat_capacity": (4.18, "kJ/kg-K"),
            "heat_of_vaporization": (2257.0, "kJ/kg"),
            "thermal_conductivity": (0.598, "W/m-K"),
        },
        "antoine": {"A": 8.07131, "B": 1730.63, "C": 233.426, "temperature_min_c": 1.0, "temperature_max_c": 100.0},
    },
    "ethylene_oxide": {
        "aliases": ["oxirane"],
        "formula": "C2H4O",
        "cas_number": "75-21-8",
        "properties": {
            "molecular_weight": (44.05, "g/mol"),
            "normal_boiling_point": (10.7, "C"),
            "melting_point": (-111.0, "C"),
            "liquid_density": (882.0, "kg/m3"),
            "liquid_viscosity": (0.0012, "Pa.s"),
            "liquid_heat_capacity": (2.23, "kJ/kg-K"),
            "heat_of_vaporization": (560.0, "kJ/kg"),
            "thermal_conductivity": (0.14, "W/m-K"),
        },
    },
    "ethylene_glycol": {
        "aliases": ["monoethylene_glycol", "meg"],
        "formula": "C2H6O2",
        "cas_number": "107-21-1",
        "properties": {
            "molecular_weight": (62.07, "g/mol"),
            "normal_boiling_point": (197.3, "C"),
            "melting_point": (-12.9, "C"),
            "liquid_density": (1113.0, "kg/m3"),
            "liquid_viscosity": (0.0161, "Pa.s"),
            "liquid_heat_capacity": (2.42, "kJ/kg-K"),
            "heat_of_vaporization": (800.0, "kJ/kg"),
            "thermal_conductivity": (0.258, "W/m-K"),
        },
    },
    "ethylene": {
        "aliases": ["c2h4"],
        "formula": "C2H4",
        "cas_number": "74-85-1",
        "properties": {
            "molecular_weight": (28.05, "g/mol"),
            "normal_boiling_point": (-103.7, "C"),
            "melting_point": (-169.2, "C"),
            "liquid_density": (1.18, "kg/m3"),
            "liquid_viscosity": (1.0e-05, "Pa.s"),
            "liquid_heat_capacity": (1.70, "kJ/kg-K"),
            "heat_of_vaporization": (480.0, "kJ/kg"),
            "thermal_conductivity": (0.034, "W/m-K"),
        },
    },
    "oxygen": {
        "aliases": ["o2"],
        "formula": "O2",
        "cas_number": "7782-44-7",
        "properties": {
            "molecular_weight": (32.0, "g/mol"),
            "normal_boiling_point": (-183.0, "C"),
            "melting_point": (-218.8, "C"),
            "liquid_density": (1.33, "kg/m3"),
            "liquid_viscosity": (2.0e-05, "Pa.s"),
            "liquid_heat_capacity": (0.92, "kJ/kg-K"),
            "heat_of_vaporization": (213.0, "kJ/kg"),
            "thermal_conductivity": (0.026, "W/m-K"),
        },
    },
    "hydrogen": {
        "aliases": ["h2"],
        "formula": "H2",
        "cas_number": "1333-74-0",
        "properties": {
            "molecular_weight": (2.016, "g/mol"),
            "normal_boiling_point": (-252.9, "C"),
            "melting_point": (-259.2, "C"),
            "liquid_density": (70.8, "kg/m3"),
            "liquid_viscosity": (8.9e-06, "Pa.s"),
            "liquid_heat_capacity": (14.30, "kJ/kg-K"),
            "heat_of_vaporization": (446.0, "kJ/kg"),
            "thermal_conductivity": (0.180, "W/m-K"),
        },
    },
    "ethylene_chlorohydrin": {
        "aliases": ["2-chloroethanol"],
        "formula": "C2H5ClO",
        "cas_number": "107-07-3",
        "properties": {
            "molecular_weight": (80.51, "g/mol"),
            "normal_boiling_point": (128.0, "C"),
            "melting_point": (-67.0, "C"),
            "liquid_density": (1200.0, "kg/m3"),
            "liquid_viscosity": (0.0031, "Pa.s"),
            "liquid_heat_capacity": (2.10, "kJ/kg-K"),
            "heat_of_vaporization": (430.0, "kJ/kg"),
            "thermal_conductivity": (0.16, "W/m-K"),
        },
    },
    "sodium_hydroxide": {
        "aliases": ["naoh", "caustic_soda"],
        "formula": "NaOH",
        "cas_number": "1310-73-2",
        "properties": {
            "molecular_weight": (40.0, "g/mol"),
            "normal_boiling_point": (1388.0, "C"),
            "melting_point": (318.0, "C"),
            "liquid_density": (2130.0, "kg/m3"),
            "liquid_viscosity": (0.012, "Pa.s"),
            "liquid_heat_capacity": (1.50, "kJ/kg-K"),
            "heat_of_vaporization": (0.0, "kJ/kg"),
            "thermal_conductivity": (0.50, "W/m-K"),
        },
    },
    "sodium_chloride": {
        "aliases": ["nacl", "salt"],
        "formula": "NaCl",
        "cas_number": "7647-14-5",
        "properties": {
            "molecular_weight": (58.44, "g/mol"),
            "normal_boiling_point": (1465.0, "C"),
            "melting_point": (801.0, "C"),
            "liquid_density": (2160.0, "kg/m3"),
            "liquid_viscosity": (0.0045, "Pa.s"),
            "liquid_heat_capacity": (0.86, "kJ/kg-K"),
            "heat_of_vaporization": (0.0, "kJ/kg"),
            "thermal_conductivity": (6.5, "W/m-K"),
        },
    },
    "methanol": {
        "aliases": ["ch4o", "methyl_alcohol"],
        "formula": "CH4O",
        "cas_number": "67-56-1",
        "properties": {
            "molecular_weight": (32.04, "g/mol"),
            "normal_boiling_point": (64.7, "C"),
            "melting_point": (-97.6, "C"),
            "liquid_density": (792.0, "kg/m3"),
            "liquid_viscosity": (0.00059, "Pa.s"),
            "liquid_heat_capacity": (2.53, "kJ/kg-K"),
            "heat_of_vaporization": (1100.0, "kJ/kg"),
            "thermal_conductivity": (0.20, "W/m-K"),
        },
        "antoine": {"A": 8.0724, "B": 1574.99, "C": 238.0, "temperature_min_c": 10.0, "temperature_max_c": 90.0},
    },
    "ethanol": {
        "aliases": ["ethyl_alcohol", "c2h6o"],
        "formula": "C2H6O",
        "cas_number": "64-17-5",
        "properties": {
            "molecular_weight": (46.07, "g/mol"),
            "normal_boiling_point": (78.4, "C"),
            "melting_point": (-114.1, "C"),
            "liquid_density": (789.0, "kg/m3"),
            "liquid_viscosity": (0.00107, "Pa.s"),
            "liquid_heat_capacity": (2.44, "kJ/kg-K"),
            "heat_of_vaporization": (846.0, "kJ/kg"),
            "thermal_conductivity": (0.171, "W/m-K"),
        },
        "antoine": {"A": 8.20417, "B": 1642.89, "C": 230.3, "temperature_min_c": 0.0, "temperature_max_c": 78.0},
    },
    "isopropanol": {
        "aliases": ["isopropyl_alcohol", "ipa", "2_propanol", "propan_2_ol", "c3h8o"],
        "formula": "C3H8O",
        "cas_number": "67-63-0",
        "properties": {
            "molecular_weight": (60.10, "g/mol"),
            "normal_boiling_point": (82.6, "C"),
            "melting_point": (-89.5, "C"),
            "liquid_density": (786.0, "kg/m3"),
            "liquid_viscosity": (0.00204, "Pa.s"),
            "liquid_heat_capacity": (2.68, "kJ/kg-K"),
            "heat_of_vaporization": (665.0, "kJ/kg"),
            "thermal_conductivity": (0.13, "W/m-K"),
        },
        "antoine": {"A": 8.11778, "B": 1580.92, "C": 219.61, "temperature_min_c": 0.0, "temperature_max_c": 90.0},
    },
    "benzene": {
        "aliases": ["c6h6"],
        "formula": "C6H6",
        "cas_number": "71-43-2",
        "properties": {
            "molecular_weight": (78.11, "g/mol"),
            "normal_boiling_point": (80.1, "C"),
            "melting_point": (5.5, "C"),
            "liquid_density": (876.0, "kg/m3"),
            "liquid_viscosity": (0.00060, "Pa.s"),
            "liquid_heat_capacity": (1.74, "kJ/kg-K"),
            "heat_of_vaporization": (394.0, "kJ/kg"),
            "thermal_conductivity": (0.167, "W/m-K"),
        },
        "antoine": {"A": 6.90565, "B": 1211.033, "C": 220.79, "temperature_min_c": 7.0, "temperature_max_c": 104.0},
    },
    "benzyl_chloride": {
        "aliases": ["chloromethylbenzene", "c7h7cl"],
        "formula": "C7H7Cl",
        "cas_number": "100-44-7",
        "properties": {
            "molecular_weight": (126.58, "g/mol"),
            "normal_boiling_point": (179.0, "C"),
            "melting_point": (-39.0, "C"),
            "liquid_density": (1100.0, "kg/m3"),
            "liquid_viscosity": (0.0013, "Pa.s"),
            "liquid_heat_capacity": (1.55, "kJ/kg-K"),
            "heat_of_vaporization": (330.0, "kJ/kg"),
            "thermal_conductivity": (0.14, "W/m-K"),
        },
    },
    "benzyl_alcohol": {
        "aliases": ["phenylmethanol", "c7h8o"],
        "formula": "C7H8O",
        "cas_number": "100-51-6",
        "properties": {
            "molecular_weight": (108.14, "g/mol"),
            "normal_boiling_point": (205.3, "C"),
            "melting_point": (-15.3, "C"),
            "liquid_density": (1045.0, "kg/m3"),
            "liquid_viscosity": (0.0055, "Pa.s"),
            "liquid_heat_capacity": (1.76, "kJ/kg-K"),
            "heat_of_vaporization": (430.0, "kJ/kg"),
            "thermal_conductivity": (0.17, "W/m-K"),
        },
    },
    "hydrogen_chloride": {
        "aliases": ["hcl", "anhydrous_hcl", "hydrochloric_acid_gas"],
        "formula": "HCl",
        "cas_number": "7647-01-0",
        "properties": {
            "molecular_weight": (36.46, "g/mol"),
            "normal_boiling_point": (-85.1, "C"),
            "melting_point": (-114.2, "C"),
            "liquid_density": (1190.0, "kg/m3"),
            "liquid_viscosity": (0.00013, "Pa.s"),
            "liquid_heat_capacity": (1.10, "kJ/kg-K"),
            "heat_of_vaporization": (410.0, "kJ/kg"),
            "thermal_conductivity": (0.10, "W/m-K"),
        },
    },
    "cumene": {
        "aliases": ["isopropylbenzene", "c9h12"],
        "formula": "C9H12",
        "cas_number": "98-82-8",
        "properties": {
            "molecular_weight": (120.19, "g/mol"),
            "normal_boiling_point": (152.4, "C"),
            "melting_point": (-96.0, "C"),
            "liquid_density": (862.0, "kg/m3"),
            "liquid_viscosity": (0.00082, "Pa.s"),
            "liquid_heat_capacity": (1.92, "kJ/kg-K"),
            "heat_of_vaporization": (356.0, "kJ/kg"),
            "thermal_conductivity": (0.129, "W/m-K"),
        },
    },
    "phenol": {
        "aliases": ["hydroxybenzene", "c6h6o"],
        "formula": "C6H6O",
        "cas_number": "108-95-2",
        "properties": {
            "molecular_weight": (94.11, "g/mol"),
            "normal_boiling_point": (181.7, "C"),
            "melting_point": (40.5, "C"),
            "liquid_density": (1070.0, "kg/m3"),
            "liquid_viscosity": (0.0038, "Pa.s"),
            "liquid_heat_capacity": (2.10, "kJ/kg-K"),
            "heat_of_vaporization": (585.0, "kJ/kg"),
            "thermal_conductivity": (0.160, "W/m-K"),
        },
    },
    "acetone": {
        "aliases": ["propanone", "c3h6o"],
        "formula": "C3H6O",
        "cas_number": "67-64-1",
        "properties": {
            "molecular_weight": (58.08, "g/mol"),
            "normal_boiling_point": (56.1, "C"),
            "melting_point": (-94.7, "C"),
            "liquid_density": (784.0, "kg/m3"),
            "liquid_viscosity": (0.00032, "Pa.s"),
            "liquid_heat_capacity": (2.16, "kJ/kg-K"),
            "heat_of_vaporization": (518.0, "kJ/kg"),
            "thermal_conductivity": (0.160, "W/m-K"),
        },
        "antoine": {"A": 7.02447, "B": 1161.0, "C": 224.0, "temperature_min_c": -10.0, "temperature_max_c": 95.0},
    },
    "alkyldimethylamine": {
        "aliases": [
            "c16h35n",
            "c14h31n",
            "lauryldimethylamine",
            "dodecyldimethylamine",
            "dimethyldodecylamine",
            "alkyldimethylamine_c12",
            "alkyldimethylamine_c12_c14",
            "c12_c14_alkyldimethylamine",
            "alkyldimethylamine_c12_c16",
        ],
        "formula": "C14H31N",
        "cas_number": "112-69-6",
        "properties": {
            "molecular_weight": (213.41, "g/mol"),
            "normal_boiling_point": (257.0, "C"),
            "melting_point": (18.0, "C"),
            "liquid_density": (790.0, "kg/m3"),
            "liquid_viscosity": (0.0033, "Pa.s"),
            "liquid_heat_capacity": (2.10, "kJ/kg-K"),
            "heat_of_vaporization": (365.0, "kJ/kg"),
            "thermal_conductivity": (0.14, "W/m-K"),
        },
    },
    "dimethylcetylamine": {
        "aliases": ["cetyl_dimethylamine", "hexadecyldimethylamine", "c18h39n"],
        "formula": "C18H39N",
        "cas_number": "112-69-6",
        "properties": {
            "molecular_weight": (269.51, "g/mol"),
            "normal_boiling_point": (318.0, "C"),
            "melting_point": (28.0, "C"),
            "liquid_density": (805.0, "kg/m3"),
            "liquid_viscosity": (0.0048, "Pa.s"),
            "liquid_heat_capacity": (2.15, "kJ/kg-K"),
            "heat_of_vaporization": (385.0, "kJ/kg"),
            "thermal_conductivity": (0.14, "W/m-K"),
        },
    },
    "benzalkonium_chloride": {
        "aliases": [
            "bkc",
            "alkyldimethylbenzylammonium_chloride",
            "benzalkonium_chloride_c12",
            "benzalkonium chloride (c12)",
            "dodecyl_benzyl_dimethyl_ammonium_chloride",
            "c23h42cln",
        ],
        "formula": "C23H42ClN",
        "cas_number": "8001-54-5",
        "properties": {
            "molecular_weight": (368.04, "g/mol"),
            "normal_boiling_point": (999.0, "C"),
            "melting_point": (-5.0, "C"),
            "liquid_density": (995.0, "kg/m3"),
            "liquid_viscosity": (0.0025, "Pa.s"),
            "liquid_heat_capacity": (3.00, "kJ/kg-K"),
            "heat_of_vaporization": (0.0, "kJ/kg"),
            "thermal_conductivity": (0.20, "W/m-K"),
        },
    },
    "cetalkonium_chloride": {
        "aliases": [
            "cetalkonium_chloride_c16_bkc",
            "cetalkonium chloride (c16 bkc)",
            "cetalkonium chloride",
            "hexadecyl_benzyl_dimethyl_ammonium_chloride",
            "c25h46cln",
        ],
        "formula": "C25H46ClN",
        "cas_number": None,
        "properties": {
            "molecular_weight": (396.10, "g/mol"),
            "normal_boiling_point": (999.0, "C"),
            "melting_point": (18.0, "C"),
            "liquid_density": (990.0, "kg/m3"),
            "liquid_viscosity": (0.0032, "Pa.s"),
            "liquid_heat_capacity": (2.95, "kJ/kg-K"),
            "heat_of_vaporization": (0.0, "kJ/kg"),
            "thermal_conductivity": (0.20, "W/m-K"),
        },
    },
    "ethyl_acetate": {
        "aliases": ["c4h8o2"],
        "formula": "C4H8O2",
        "cas_number": "141-78-6",
        "properties": {
            "molecular_weight": (88.11, "g/mol"),
            "normal_boiling_point": (77.1, "C"),
            "melting_point": (-83.6, "C"),
            "liquid_density": (897.0, "kg/m3"),
            "liquid_viscosity": (0.00045, "Pa.s"),
            "liquid_heat_capacity": (1.79, "kJ/kg-K"),
            "heat_of_vaporization": (365.0, "kJ/kg"),
            "thermal_conductivity": (0.144, "W/m-K"),
        },
        "antoine": {"A": 7.10179, "B": 1244.951, "C": 217.881, "temperature_min_c": -5.0, "temperature_max_c": 90.0},
    },
    "chlorobenzene": {
        "aliases": ["c6h5cl"],
        "formula": "C6H5Cl",
        "cas_number": "108-90-7",
        "properties": {
            "molecular_weight": (112.56, "g/mol"),
            "normal_boiling_point": (131.7, "C"),
            "melting_point": (-45.6, "C"),
            "liquid_density": (1106.0, "kg/m3"),
            "liquid_viscosity": (0.00076, "Pa.s"),
            "liquid_heat_capacity": (1.06, "kJ/kg-K"),
            "heat_of_vaporization": (330.0, "kJ/kg"),
            "thermal_conductivity": (0.137, "W/m-K"),
        },
    },
    "carbon_monoxide": {
        "aliases": ["co"],
        "formula": "CO",
        "cas_number": "630-08-0",
        "properties": {
            "molecular_weight": (28.01, "g/mol"),
            "normal_boiling_point": (-191.5, "C"),
            "melting_point": (-205.0, "C"),
            "liquid_density": (1.15, "kg/m3"),
            "liquid_viscosity": (1.7e-05, "Pa.s"),
            "liquid_heat_capacity": (1.04, "kJ/kg-K"),
            "heat_of_vaporization": (216.0, "kJ/kg"),
            "thermal_conductivity": (0.025, "W/m-K"),
        },
    },
    "acetic_acid": {
        "aliases": ["ethanoic_acid"],
        "formula": "C2H4O2",
        "cas_number": "64-19-7",
        "properties": {
            "molecular_weight": (60.05, "g/mol"),
            "normal_boiling_point": (118.1, "C"),
            "melting_point": (16.6, "C"),
            "liquid_density": (1049.0, "kg/m3"),
            "liquid_viscosity": (0.00122, "Pa.s"),
            "liquid_heat_capacity": (2.05, "kJ/kg-K"),
            "heat_of_vaporization": (390.0, "kJ/kg"),
            "thermal_conductivity": (0.18, "W/m-K"),
        },
        "antoine": {"A": 7.6377, "B": 1336.46, "C": 199.2, "temperature_min_c": 10.0, "temperature_max_c": 120.0},
    },
    "acetaldehyde": {
        "aliases": ["ethanal"],
        "formula": "C2H4O",
        "cas_number": "75-07-0",
        "properties": {
            "molecular_weight": (44.05, "g/mol"),
            "normal_boiling_point": (20.2, "C"),
            "melting_point": (-123.5, "C"),
            "liquid_density": (784.0, "kg/m3"),
            "liquid_viscosity": (0.00022, "Pa.s"),
            "liquid_heat_capacity": (2.10, "kJ/kg-K"),
            "heat_of_vaporization": (540.0, "kJ/kg"),
            "thermal_conductivity": (0.17, "W/m-K"),
        },
    },
    "n_butane": {
        "aliases": ["butane", "c4h10"],
        "formula": "C4H10",
        "cas_number": "106-97-8",
        "properties": {
            "molecular_weight": (58.12, "g/mol"),
            "normal_boiling_point": (-0.5, "C"),
            "melting_point": (-138.4, "C"),
            "liquid_density": (2.48, "kg/m3"),
            "liquid_viscosity": (8.0e-06, "Pa.s"),
            "liquid_heat_capacity": (1.72, "kJ/kg-K"),
            "heat_of_vaporization": (365.0, "kJ/kg"),
            "thermal_conductivity": (0.016, "W/m-K"),
        },
    },
    "carbon_dioxide": {
        "aliases": ["co2"],
        "formula": "CO2",
        "cas_number": "124-38-9",
        "properties": {
            "molecular_weight": (44.01, "g/mol"),
            "normal_boiling_point": (-78.5, "C"),
            "melting_point": (-56.6, "C"),
            "liquid_density": (1.84, "kg/m3"),
            "liquid_viscosity": (1.5e-05, "Pa.s"),
            "liquid_heat_capacity": (0.84, "kJ/kg-K"),
            "heat_of_vaporization": (235.0, "kJ/kg"),
            "thermal_conductivity": (0.017, "W/m-K"),
        },
    },
    "formic_acid": {
        "aliases": ["methanoic_acid"],
        "formula": "CH2O2",
        "cas_number": "64-18-6",
        "properties": {
            "molecular_weight": (46.03, "g/mol"),
            "normal_boiling_point": (100.8, "C"),
            "melting_point": (8.4, "C"),
            "liquid_density": (1220.0, "kg/m3"),
            "liquid_viscosity": (0.0016, "Pa.s"),
            "liquid_heat_capacity": (2.20, "kJ/kg-K"),
            "heat_of_vaporization": (470.0, "kJ/kg"),
            "thermal_conductivity": (0.20, "W/m-K"),
        },
    },
    "propionic_acid": {
        "aliases": ["propanoic_acid"],
        "formula": "C3H6O2",
        "cas_number": "79-09-4",
        "properties": {
            "molecular_weight": (74.08, "g/mol"),
            "normal_boiling_point": (141.1, "C"),
            "melting_point": (-20.8, "C"),
            "liquid_density": (993.0, "kg/m3"),
            "liquid_viscosity": (0.0010, "Pa.s"),
            "liquid_heat_capacity": (2.10, "kJ/kg-K"),
            "heat_of_vaporization": (420.0, "kJ/kg"),
            "thermal_conductivity": (0.16, "W/m-K"),
        },
    },
    "sulfur_dioxide": {
        "aliases": ["so2"],
        "formula": "SO2",
        "cas_number": "7446-09-5",
        "properties": {
            "molecular_weight": (64.07, "g/mol"),
            "normal_boiling_point": (-10.0, "C"),
            "melting_point": (-72.7, "C"),
            "liquid_density": (2.62, "kg/m3"),
            "liquid_viscosity": (1.2e-05, "Pa.s"),
            "liquid_heat_capacity": (0.65, "kJ/kg-K"),
            "heat_of_vaporization": (390.0, "kJ/kg"),
            "thermal_conductivity": (0.013, "W/m-K"),
        },
    },
    "sulfuric_acid": {
        "aliases": ["h2so4"],
        "formula": "H2SO4",
        "cas_number": "7664-93-9",
        "properties": {
            "molecular_weight": (98.08, "g/mol"),
            "normal_boiling_point": (337.0, "C"),
            "melting_point": (10.3, "C"),
            "liquid_density": (1840.0, "kg/m3"),
            "liquid_viscosity": (0.024, "Pa.s"),
            "liquid_heat_capacity": (1.38, "kJ/kg-K"),
            "heat_of_vaporization": (510.0, "kJ/kg"),
            "thermal_conductivity": (0.36, "W/m-K"),
        },
    },
    "spent_acid": {
        "aliases": ["spent_sulfuric_acid"],
        "formula": "H2SO4",
        "cas_number": "7664-93-9",
        "properties": {
            "molecular_weight": (98.08, "g/mol"),
            "normal_boiling_point": (337.0, "C"),
            "melting_point": (10.3, "C"),
            "liquid_density": (1760.0, "kg/m3"),
            "liquid_viscosity": (0.028, "Pa.s"),
            "liquid_heat_capacity": (1.45, "kJ/kg-K"),
            "heat_of_vaporization": (480.0, "kJ/kg"),
            "thermal_conductivity": (0.35, "W/m-K"),
        },
    },
    "soda_ash": {
        "aliases": ["sodium_carbonate", "na2co3"],
        "formula": "Na2CO3",
        "cas_number": "497-19-8",
        "properties": {
            "molecular_weight": (105.99, "g/mol"),
            "normal_boiling_point": (1600.0, "C"),
            "melting_point": (851.0, "C"),
            "liquid_density": (2540.0, "kg/m3"),
            "liquid_viscosity": (0.005, "Pa.s"),
            "liquid_heat_capacity": (0.90, "kJ/kg-K"),
            "heat_of_vaporization": (0.0, "kJ/kg"),
            "thermal_conductivity": (2.6, "W/m-K"),
        },
    },
    "sodium_carbonate_liquor": {
        "aliases": ["sodium carbonate liquor"],
        "formula": "Na2CO3",
        "cas_number": "497-19-8",
        "properties": {
            "molecular_weight": (105.99, "g/mol"),
            "normal_boiling_point": (100.0, "C"),
            "melting_point": (0.0, "C"),
            "liquid_density": (1200.0, "kg/m3"),
            "liquid_viscosity": (0.0025, "Pa.s"),
            "liquid_heat_capacity": (3.10, "kJ/kg-K"),
            "heat_of_vaporization": (2100.0, "kJ/kg"),
            "thermal_conductivity": (0.45, "W/m-K"),
        },
    },
    "sodium_bicarbonate": {
        "aliases": ["nahco3", "baking_soda"],
        "formula": "NaHCO3",
        "cas_number": "144-55-8",
        "properties": {
            "molecular_weight": (84.01, "g/mol"),
            "normal_boiling_point": ("Decomposes", "-"),
            "melting_point": (50.0, "C"),
            "liquid_density": (2200.0, "kg/m3"),
            "liquid_viscosity": (0.0045, "Pa.s"),
            "liquid_heat_capacity": (0.95, "kJ/kg-K"),
            "heat_of_vaporization": (0.0, "kJ/kg"),
            "thermal_conductivity": (0.27, "W/m-K"),
        },
    },
    "ammonia": {
        "aliases": ["nh3"],
        "formula": "NH3",
        "cas_number": "7664-41-7",
        "properties": {
            "molecular_weight": (17.03, "g/mol"),
            "normal_boiling_point": (-33.3, "C"),
            "melting_point": (-77.7, "C"),
            "liquid_density": (0.73, "kg/m3"),
            "liquid_viscosity": (9.0e-06, "Pa.s"),
            "liquid_heat_capacity": (2.06, "kJ/kg-K"),
            "heat_of_vaporization": (1370.0, "kJ/kg"),
            "thermal_conductivity": (0.025, "W/m-K"),
        },
    },
    "ammonium_chloride": {
        "aliases": ["nh4cl"],
        "formula": "NH4Cl",
        "cas_number": "12125-02-9",
        "properties": {
            "molecular_weight": (53.49, "g/mol"),
            "normal_boiling_point": (520.0, "C"),
            "melting_point": (338.0, "C"),
            "liquid_density": (1530.0, "kg/m3"),
            "liquid_viscosity": (0.0042, "Pa.s"),
            "liquid_heat_capacity": (1.40, "kJ/kg-K"),
            "heat_of_vaporization": (0.0, "kJ/kg"),
            "thermal_conductivity": (0.51, "W/m-K"),
        },
    },
}

BENCHMARK_BINARY_INTERACTION_LIBRARY: dict[tuple[str, str], dict[str, object]] = {
    ("alkyldimethylamine", "benzyl_chloride"): {
        "component_a": "Alkyldimethylamine",
        "component_b": "Benzyl chloride",
        "model_name": "NRTL",
        "tau12": 0.55,
        "tau21": 1.45,
        "alpha12": 0.32,
        "source_ids": ["seed_bip_bac_cleanup"],
    },
    ("alkyldimethylamine", "ethanol"): {
        "component_a": "Alkyldimethylamine",
        "component_b": "Ethanol",
        "model_name": "NRTL",
        "tau12": 0.70,
        "tau21": 0.95,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_cleanup"],
    },
    ("alkyldimethylamine", "water"): {
        "component_a": "Alkyldimethylamine",
        "component_b": "Water",
        "model_name": "NRTL",
        "tau12": 1.10,
        "tau21": 0.85,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_cleanup"],
    },
    ("alkyldimethylamine", "benzyl_alcohol"): {
        "component_a": "Alkyldimethylamine",
        "component_b": "Benzyl alcohol",
        "model_name": "NRTL",
        "tau12": 0.82,
        "tau21": 0.66,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_cleanup"],
    },
    ("alkyldimethylamine", "benzalkonium_chloride"): {
        "component_a": "Alkyldimethylamine",
        "component_b": "Benzalkonium chloride",
        "model_name": "NRTL",
        "tau12": 1.35,
        "tau21": -0.20,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_active_solution"],
    },
    ("benzalkonium_chloride", "benzyl_alcohol"): {
        "component_a": "Benzalkonium chloride",
        "component_b": "Benzyl alcohol",
        "model_name": "NRTL",
        "tau12": 0.74,
        "tau21": 0.18,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_active_solution"],
    },
    ("benzalkonium_chloride", "benzyl_chloride"): {
        "component_a": "Benzalkonium chloride",
        "component_b": "Benzyl chloride",
        "model_name": "NRTL",
        "tau12": 1.05,
        "tau21": -0.08,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_active_solution"],
    },
    ("benzalkonium_chloride", "ethanol"): {
        "component_a": "Benzalkonium chloride",
        "component_b": "Ethanol",
        "model_name": "NRTL",
        "tau12": 0.88,
        "tau21": 0.24,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_active_solution"],
    },
    ("benzalkonium_chloride", "water"): {
        "component_a": "Benzalkonium chloride",
        "component_b": "Water",
        "model_name": "NRTL",
        "tau12": 1.42,
        "tau21": 0.36,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_active_solution"],
    },
    ("benzyl_alcohol", "ethanol"): {
        "component_a": "Benzyl alcohol",
        "component_b": "Ethanol",
        "model_name": "NRTL",
        "tau12": 0.38,
        "tau21": 0.28,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_cleanup"],
    },
    ("benzyl_alcohol", "water"): {
        "component_a": "Benzyl alcohol",
        "component_b": "Water",
        "model_name": "NRTL",
        "tau12": 1.35,
        "tau21": 0.75,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_cleanup"],
    },
    ("benzyl_alcohol", "benzyl_chloride"): {
        "component_a": "Benzyl alcohol",
        "component_b": "Benzyl chloride",
        "model_name": "NRTL",
        "tau12": 0.46,
        "tau21": 0.34,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_cleanup"],
    },
    ("benzyl_chloride", "ethanol"): {
        "component_a": "Benzyl chloride",
        "component_b": "Ethanol",
        "model_name": "NRTL",
        "tau12": 0.95,
        "tau21": 0.45,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_cleanup"],
    },
    ("benzyl_chloride", "water"): {
        "component_a": "Benzyl chloride",
        "component_b": "Water",
        "model_name": "NRTL",
        "tau12": 1.60,
        "tau21": 0.95,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_bac_cleanup"],
    },
    ("ethanol", "water"): {
        "component_a": "Ethanol",
        "component_b": "Water",
        "model_name": "NRTL",
        "tau12": 0.18,
        "tau21": 1.12,
        "alpha12": 0.30,
        "source_ids": ["seed_bip_generic_polar"],
    },
}
BENCHMARK_HENRY_LIBRARY: dict[tuple[str, str], dict[str, object]] = {
    ("carbon_dioxide", "water"): {
        "value": 29.4,
        "units": "bar",
        "reference_temperature_c": 25.0,
        "equation_form": "P=H*x",
    },
    ("sulfur_dioxide", "water"): {
        "value": 1.3,
        "units": "bar",
        "reference_temperature_c": 25.0,
        "equation_form": "P=H*x",
    },
    ("sulfur_dioxide", "sulfuric_acid"): {
        "value": 0.9,
        "units": "bar",
        "reference_temperature_c": 25.0,
        "equation_form": "P=H*x",
    },
}
BENCHMARK_SOLUBILITY_LIBRARY: dict[tuple[str, str], dict[str, object]] = {
    ("sodium_bicarbonate", "water"): {
        "equation_name": "linear",
        "parameters": {"a": 0.062, "b": 0.00110},
        "temperature_min_c": 0.0,
        "temperature_max_c": 80.0,
        "units": "kg_solute_per_kg_solvent",
    },
}

_BIP_PIPE_RE = re.compile(
    r"^BIP\|(?P<model>[A-Za-z0-9_ -]+)\|(?P<component_a>[^|]+)\|(?P<component_b>[^|]+)\|(?P<params>.+)$",
    re.IGNORECASE,
)
_BIP_PARAM_RE = re.compile(r"(?P<name>tau12|tau21|alpha12|alpha)\s*=\s*(?P<value>-?\d+(?:\.\d+)?)", re.IGNORECASE)
_BIP_SENTENCE_RE = re.compile(
    r"(?P<model>NRTL)\s+(?:parameters?\s+for\s+)?(?P<component_a>[A-Za-z0-9][A-Za-z0-9 \-]+?)\s*/\s*(?P<component_b>[A-Za-z0-9][A-Za-z0-9 \-]+?)"
    r".*?tau12\s*=\s*(?P<tau12>-?\d+(?:\.\d+)?)"
    r".*?tau21\s*=\s*(?P<tau21>-?\d+(?:\.\d+)?)"
    r".*?(?:alpha12|alpha)\s*=\s*(?P<alpha>-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_HENRY_PIPE_RE = re.compile(
    r"^HENRY\|(?P<gas>[^|]+)\|(?P<solvent>[^|]+)\|(?P<params>.+)$",
    re.IGNORECASE,
)
_SOLUBILITY_PIPE_RE = re.compile(
    r"^SOLUBILITY\|(?P<solute>[^|]+)\|(?P<solvent>[^|]+)\|(?P<params>.+)$",
    re.IGNORECASE,
)
_GENERIC_PARAM_RE = re.compile(r"(?P<name>[A-Za-z0-9_]+)\s*=\s*(?P<value>-?\d+(?:\.\d+)?)", re.IGNORECASE)


def match_benchmark_entry(name: str, formula: str | None = None) -> tuple[str, dict[str, object]] | tuple[None, None]:
    normalized = normalize_chemical_name(name)
    for key, record in BENCHMARK_PROPERTY_LIBRARY.items():
        aliases = {normalize_chemical_name(alias) for alias in record.get("aliases", [])}
        if normalized == key or normalized in aliases:
            return key, record
        if formula and formula == record.get("formula"):
            return key, record
    return None, None


def _pair_key(component_a: str, component_b: str) -> tuple[str, str]:
    pair = tuple(sorted((normalize_chemical_name(component_a), normalize_chemical_name(component_b))))
    return pair[0], pair[1]


def _ordered_pair_key(component_a: str, component_b: str) -> tuple[str, str]:
    return normalize_chemical_name(component_a), normalize_chemical_name(component_b)


def _parse_bip_line(line: str) -> dict[str, object] | None:
    match = _BIP_PIPE_RE.match(line.strip())
    if match:
        params = {item.group("name").lower(): float(item.group("value")) for item in _BIP_PARAM_RE.finditer(match.group("params"))}
        if "tau12" not in params or "tau21" not in params:
            return None
        return {
            "model_name": match.group("model").strip().upper(),
            "component_a": match.group("component_a").strip(),
            "component_b": match.group("component_b").strip(),
            "tau12": params["tau12"],
            "tau21": params["tau21"],
            "alpha12": params.get("alpha12", params.get("alpha", 0.3)),
        }
    match = _BIP_SENTENCE_RE.search(line.strip())
    if not match:
        return None
    return {
        "model_name": match.group("model").strip().upper(),
        "component_a": match.group("component_a").strip(),
        "component_b": match.group("component_b").strip(),
        "tau12": float(match.group("tau12")),
        "tau21": float(match.group("tau21")),
        "alpha12": float(match.group("alpha")),
    }


def _parse_henry_line(line: str) -> dict[str, object] | None:
    match = _HENRY_PIPE_RE.match(line.strip())
    if not match:
        return None
    params = {item.group("name").lower(): float(item.group("value")) for item in _GENERIC_PARAM_RE.finditer(match.group("params"))}
    if "value" not in params and "h" not in params:
        return None
    return {
        "gas": match.group("gas").strip(),
        "solvent": match.group("solvent").strip(),
        "value": params.get("value", params.get("h")),
        "units": "bar",
        "reference_temperature_c": params.get("reference_temperature_c", params.get("t_ref", 25.0)),
        "equation_form": "P=H*x",
    }


def _parse_solubility_line(line: str) -> dict[str, object] | None:
    match = _SOLUBILITY_PIPE_RE.match(line.strip())
    if not match:
        return None
    params = {item.group("name").lower(): float(item.group("value")) for item in _GENERIC_PARAM_RE.finditer(match.group("params"))}
    if "a" not in params:
        return None
    return {
        "solute": match.group("solute").strip(),
        "solvent": match.group("solvent").strip(),
        "equation_name": "linear",
        "parameters": {"a": params["a"], "b": params.get("b", 0.0)},
        "temperature_min_c": params.get("temperature_min_c", params.get("tmin", 0.0)),
        "temperature_max_c": params.get("temperature_max_c", params.get("tmax", 100.0)),
        "units": "kg_solute_per_kg_solvent",
    }


def resolve_binary_interaction_entry(
    component_a: str,
    component_b: str,
    bundle: ResearchBundle,
) -> dict[str, object] | None:
    requested_a = normalize_chemical_name(component_a)
    requested_b = normalize_chemical_name(component_b)
    if requested_a == requested_b:
        return None
    seed_entry = BENCHMARK_BINARY_INTERACTION_LIBRARY.get(_pair_key(component_a, component_b))
    if isinstance(seed_entry, dict):
        seed = dict(seed_entry)
        source_ids = technical_anchor_source_ids(bundle) or list(seed.get("source_ids", []))
        seed.setdefault("model_name", "NRTL")
        seed["source_ids"] = source_ids
        if seed_entry.get("source_ids"):
            seed["seed_reference_ids"] = list(seed_entry.get("source_ids", []))
        if normalize_chemical_name(str(seed.get("component_a", component_a))) == requested_a:
            return seed
        return {
            **seed,
            "component_a": component_a,
            "component_b": component_b,
            "tau12": seed.get("tau21"),
            "tau21": seed.get("tau12"),
        }
    for source in bundle.sources:
        text = "\n".join(
            part for part in [source.extraction_snippet, source.citation_text]
            if part
        )
        for line in itertools.chain.from_iterable(part.splitlines() for part in [text]):
            parsed = _parse_bip_line(line)
            if not parsed:
                continue
            parsed_a = normalize_chemical_name(str(parsed["component_a"]))
            parsed_b = normalize_chemical_name(str(parsed["component_b"]))
            if {parsed_a, parsed_b} != {requested_a, requested_b}:
                continue
            source_ids = [source.source_id]
            if parsed_a == requested_a:
                return {**parsed, "source_ids": source_ids}
            return {
                **parsed,
                "component_a": component_a,
                "component_b": component_b,
                "tau12": parsed["tau21"],
                "tau21": parsed["tau12"],
                "source_ids": source_ids,
            }
    return None


def resolve_henry_entry(
    gas_component: str,
    solvent_component: str,
    bundle: ResearchBundle,
) -> dict[str, object] | None:
    seed_entry = BENCHMARK_HENRY_LIBRARY.get(_ordered_pair_key(gas_component, solvent_component))
    if isinstance(seed_entry, dict):
        return {
            **seed_entry,
            "gas": gas_component,
            "solvent": solvent_component,
            "source_ids": technical_anchor_source_ids(bundle),
        }
    requested_gas = normalize_chemical_name(gas_component)
    requested_solvent = normalize_chemical_name(solvent_component)
    for source in bundle.sources:
        text = "\n".join(part for part in [source.extraction_snippet, source.citation_text] if part)
        for line in text.splitlines():
            parsed = _parse_henry_line(line)
            if not parsed:
                continue
            if normalize_chemical_name(str(parsed["gas"])) != requested_gas:
                continue
            if normalize_chemical_name(str(parsed["solvent"])) != requested_solvent:
                continue
            return {**parsed, "source_ids": [source.source_id]}
    return None


def resolve_solubility_entry(
    solute_component: str,
    solvent_component: str,
    bundle: ResearchBundle,
) -> dict[str, object] | None:
    seed_entry = BENCHMARK_SOLUBILITY_LIBRARY.get(_ordered_pair_key(solute_component, solvent_component))
    if isinstance(seed_entry, dict):
        return {
            **seed_entry,
            "solute": solute_component,
            "solvent": solvent_component,
            "source_ids": technical_anchor_source_ids(bundle),
        }
    requested_solute = normalize_chemical_name(solute_component)
    requested_solvent = normalize_chemical_name(solvent_component)
    for source in bundle.sources:
        text = "\n".join(part for part in [source.extraction_snippet, source.citation_text] if part)
        for line in text.splitlines():
            parsed = _parse_solubility_line(line)
            if not parsed:
                continue
            if normalize_chemical_name(str(parsed["solute"])) != requested_solute:
                continue
            if normalize_chemical_name(str(parsed["solvent"])) != requested_solvent:
                continue
            return {**parsed, "source_ids": [source.source_id]}
    return None


def product_profile_source_index(product_profile: ProductProfileArtifact) -> dict[str, list[str]]:
    return {
        normalize_chemical_name(item.name): list(dict.fromkeys(item.supporting_sources or item.citations))
        for item in product_profile.properties
    }


def technical_anchor_source_ids(bundle: ResearchBundle, limit: int = 2) -> list[str]:
    anchors = bundle.technical_source_ids or [source.source_id for source in bundle.sources[:limit]]
    return list(dict.fromkeys(anchors[:limit]))


def _merge_identifier_spec(
    route_map: dict[str, dict[str, object]],
    *,
    canonical_name: str,
    route_id: str = "",
    formula: str | None = None,
) -> None:
    if not is_valid_property_identifier_name(canonical_name):
        return
    normalized = normalize_chemical_name(canonical_name)
    benchmark_key, benchmark_record = match_benchmark_entry(canonical_name, formula)
    resolved_formula = formula or (str(benchmark_record.get("formula")) if benchmark_record else None)
    resolved_name = canonical_name
    if benchmark_key and benchmark_record:
        resolved_name = str(benchmark_record.get("aliases", [canonical_name])[0]) if benchmark_record.get("aliases") else canonical_name
        resolved_name = canonical_name if normalize_chemical_name(canonical_name) == benchmark_key else resolved_name
    entry = route_map.setdefault(
        normalized,
        {
            "canonical_name": canonical_name,
            "aliases": set(),
            "formula": resolved_formula,
            "route_ids": set(),
        },
    )
    entry["aliases"].add(canonical_name)
    if route_id:
        entry["route_ids"].add(route_id)
    if not entry.get("formula") and resolved_formula:
        entry["formula"] = resolved_formula
    if entry.get("canonical_name") == canonical_name and benchmark_record and benchmark_key:
        entry["aliases"].add(benchmark_key.replace("_", " "))


def _add_known_byproduct_mentions(
    route_map: dict[str, dict[str, object]],
    *,
    text: str,
    route_id: str,
) -> None:
    lowered = text.lower()
    for key, record in BENCHMARK_PROPERTY_LIBRARY.items():
        phrases = {key.replace("_", " ")}
        phrases.update(str(alias).lower() for alias in record.get("aliases", []))
        if any(re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", lowered) for phrase in phrases if len(phrase) >= 4):
            _merge_identifier_spec(
                route_map,
                canonical_name=key.replace("_", " "),
                route_id=route_id,
                formula=str(record.get("formula") or ""),
            )


def collect_identifier_specs(product_profile: ProductProfileArtifact, route_survey: RouteSurveyArtifact | None) -> list[dict[str, object]]:
    route_map: dict[str, dict[str, object]] = {}
    if route_survey is not None:
        for route in route_survey.routes:
            for participant in route.participants:
                _merge_identifier_spec(
                    route_map,
                    canonical_name=participant.name,
                    route_id=route.route_id,
                    formula=participant.formula,
                )
            for solvent in getattr(route, "solvents", []):
                _merge_identifier_spec(route_map, canonical_name=solvent, route_id=route.route_id)
            for byproduct in route.byproducts:
                _add_known_byproduct_mentions(route_map, text=byproduct, route_id=route.route_id)
    specs: list[dict[str, object]] = [
        {
            "canonical_name": product_profile.product_name,
            "aliases": {product_profile.product_name},
            "formula": None,
            "route_ids": set(),
        }
    ]
    for carrier in getattr(product_profile, "carrier_components", []):
        _merge_identifier_spec(route_map, canonical_name=carrier)
    seen = {normalize_chemical_name(product_profile.product_name)}
    for normalized, entry in route_map.items():
        if normalized in seen:
            specs[0]["aliases"].update(entry["aliases"])
            specs[0]["route_ids"].update(entry["route_ids"])
            if entry.get("formula") and not specs[0].get("formula"):
                specs[0]["formula"] = entry["formula"]
            continue
        specs.append(entry)
        seen.add(normalized)
    normalized_specs: list[dict[str, object]] = []
    for spec in specs:
        normalized_specs.append(
            {
                "identifier_id": normalize_chemical_name(str(spec["canonical_name"])),
                "canonical_name": str(spec["canonical_name"]),
                "aliases": sorted({str(alias) for alias in spec.get("aliases", set()) if str(alias).strip()}),
                "formula": spec.get("formula"),
                "route_ids": sorted({str(route_id) for route_id in spec.get("route_ids", set())}),
            }
        )
    return normalized_specs
