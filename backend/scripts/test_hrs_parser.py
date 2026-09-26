import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


# from hrs.parser import (
#     parse_hrs_variable,
# )


# def main():

#     variables = [
#         "R1MSTAT",
#         "R15MSTAT",
#         "S1BMONTH",
#         "HHIDPN",
#         "R99ABC",
#     ]

#     print(
#         "\n=== HRS VARIABLE PARSER ==="
#     )

#     for name in variables:

#         parsed = (
#             parse_hrs_variable(name)
#         )

#         print(
#             f"\n{name}"
#         )

#         print(
#             "  role:",
#             parsed.role,
#         )

#         print(
#             "  wave:",
#             parsed.wave,
#         )

#         print(
#             "  year:",
#             parsed.year,
#         )

#         print(
#             "  base_name:",
#             parsed.base_name,
#         )

#         print(
#             "  wave_specific:",
#             parsed.is_wave_specific,
#         )


# if __name__ == "__main__":
#     main()

from hrs.parser import parse_hrs_variable


TEST_VARIABLES = [
    "R1MSTAT",
    "R15MSTAT",
    "S1BMONTH",
    "H15ANYFIN",
    "RAGENDER",
    "RABYEAR",
    "REMSTAT",
    "INW1",
    "INW15",
    "INW16",
    "HHIDPN",
]


def main():

    for name in TEST_VARIABLES:

        parsed = parse_hrs_variable(name)

        print("=" * 60)
        print("name:", parsed.name)
        print("role:", parsed.role)
        print("wave:", parsed.wave)
        print("year:", parsed.year)
        print("years:", parsed.years)
        print("base_name:", parsed.base_name)
        print("variable_scope:", parsed.variable_scope)
        print(
            "is_wave_specific:",
            parsed.is_wave_specific,
        )


if __name__ == "__main__":
    main()