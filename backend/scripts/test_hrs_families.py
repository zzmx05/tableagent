import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from hrs.catalog import HRSVariableCatalog
from hrs.families import HRSVariableFamilyIndex


METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "hrs_variables.json"
)


def print_family(
    family,
):

    if family is None:

        print(
            "Family not found."
        )

        return

    print(
        "\n=== VARIABLE FAMILY ==="
    )

    print(
        "Role:",
        family.role,
    )

    print(
        "Base name:",
        family.base_name,
    )

    print(
        "Wave count:",
        family.wave_count,
    )

    print(
        "Waves:",
        family.waves,
    )

    print(
        "\nMembers:"
    )

    for member in family.members:

        print(
            f"W{member.wave:<3}"
            f"{str(member.years):<15}"
            f"{member.name:<15}"
            f"{member.label}"
        )


def main():

    catalog = HRSVariableCatalog(
        METADATA_PATH
    )

    families = HRSVariableFamilyIndex(
        catalog
    )

    print(
        "Family count:",
        families.family_count,
    )

    family = families.get_family(
        role="respondent",
        base_name="MSTAT",
    )

    print_family(
        family
    )

    print(
        "\n=== FAMILY FROM VARIABLE ==="
    )

    family = (
        families.get_family_for_variable(
            "R15MSTAT"
        )
    )

    print_family(
        family
    )


if __name__ == "__main__":
    main()