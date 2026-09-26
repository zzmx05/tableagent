import sys
from collections import Counter, defaultdict
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


def main():

    catalog = HRSVariableCatalog(
        METADATA_PATH
    )

    families = HRSVariableFamilyIndex(
        catalog
    )

    # -----------------------------------------------------
    # Basic counts
    # -----------------------------------------------------

    role_counts = Counter()

    wave_count_distribution = Counter()

    complete_families = []

    single_wave_families = []

    duplicate_wave_families = []

    # -----------------------------------------------------
    # Diagnose every family
    # -----------------------------------------------------

    for family in families.families:

        role_counts[
            family.role
        ] += 1

        wave_count_distribution[
            family.wave_count
        ] += 1

        if family.wave_count == 16:

            complete_families.append(
                family
            )

        if family.wave_count == 1:

            single_wave_families.append(
                family
            )

        # ---------------------------------------------
        # Check whether one family contains multiple
        # variables for the same wave.
        # ---------------------------------------------

        members_by_wave = defaultdict(
            list
        )

        for member in family.members:

            members_by_wave[
                member.wave
            ].append(
                member.name
            )

        duplicates = {
            wave: names
            for wave, names
            in members_by_wave.items()
            if len(names) > 1
        }

        if duplicates:

            duplicate_wave_families.append(
                (
                    family,
                    duplicates,
                )
            )

    # -----------------------------------------------------
    # Output
    # -----------------------------------------------------

    print(
        "\n=== HRS VARIABLE FAMILY DIAGNOSTIC ==="
    )

    print(
        "Total variables:",
        catalog.variable_count,
    )

    print(
        "Total families:",
        families.family_count,
    )

    print(
        "\n=== FAMILY ROLE COUNTS ==="
    )

    for role, count in sorted(
        role_counts.items()
    ):

        print(
            f"{role:<15} {count}"
        )

    print(
        "\n=== FAMILY WAVE COUNT DISTRIBUTION ==="
    )

    for wave_count in sorted(
        wave_count_distribution
    ):

        print(
            f"{wave_count:>2} waves: "
            f"{wave_count_distribution[wave_count]}"
        )

    print(
        "\nComplete 16-wave families:",
        len(complete_families),
    )

    print(
        "Single-wave families:",
        len(single_wave_families),
    )

    print(
        "Families with duplicate wave members:",
        len(duplicate_wave_families),
    )

    # -----------------------------------------------------
    # Show complete families
    # -----------------------------------------------------

    print(
        "\n=== FIRST 50 COMPLETE FAMILIES ==="
    )

    for family in complete_families[:50]:

        print(
            f"{family.role:<12}"
            f"{family.base_name:<20}"
            f"{family.variable_names}"
        )

    # -----------------------------------------------------
    # Show single-wave families
    # -----------------------------------------------------

    print(
        "\n=== FIRST 50 SINGLE-WAVE FAMILIES ==="
    )

    for family in single_wave_families[:50]:

        member = family.members[0]

        print(
            f"{family.role:<12}"
            f"{family.base_name:<20}"
            f"W{member.wave:<3}"
            f"{member.name:<15}"
            f"{member.label}"
        )

    # -----------------------------------------------------
    # Show duplicate-wave families
    # -----------------------------------------------------

    print(
        "\n=== DUPLICATE WAVE MEMBERS ==="
    )

    for (
        family,
        duplicates,
    ) in duplicate_wave_families[:50]:

        print(
            "\nFamily:",
            family.role,
            family.base_name,
        )

        for wave, names in sorted(
            duplicates.items()
        ):

            print(
                f"  W{wave}: "
                f"{names}"
            )


if __name__ == "__main__":
    main()