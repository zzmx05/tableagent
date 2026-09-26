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
from hrs.semantic import HRSSemanticSearch


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

    semantic = HRSSemanticSearch(
        catalog,
        families,
    )

    queries = [
        "MSTAT",
        "marital status",
        "depressed",
        "cognition",
        "retirement",
    ]

    for query in queries:

        print("\n"+ "=" * 70)

        print(
            "QUERY:",
            query,
        )

        results = (
            semantic.search_families(
                query,
                limit=10,
            )
        )

        for result in results:

            print(
                f"{result.score:<4}"
                f"{result.role:<12}"
                f"{result.base_name:<20}"
                f"{result.match_type:<18}"
                f"waves={result.family.wave_count}"
            )
        
            print(
                "\n"
                + "=" * 70
            )

            print(
                "FAMILY YEAR / WAVE LOOKUP"
            )

            family = families.get_family(
                role="respondent",
                base_name="MSTAT",
            )

            if family is None:

                print(
                    "MSTAT family not found."
                )

                return

            member_2020 = (
                family.get_member_for_year(
                    2020
                )
            )

            member_1993 = (
                family.get_member_for_year(
                    1993
                )
            )

            member_wave16 = (
                family.get_member_for_wave(
                    16
                )
            )

            members_10_to_16 = (
                family.get_members_for_waves(
                    (
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                    )
                )
            )

            print(
                "2020:",
                (
                    member_2020.name
                    if member_2020
                    else None
                )
            )

            print(
                "1993:",
                (
                    member_1993.name
                    if member_1993
                    else None
                )
            )

            print(
                "Wave 16:",
                (
                    member_wave16.name
                    if member_wave16
                    else None
                )
            )

            print(
                "Waves 10-16:",
                tuple(
                    member.name
                    for member
                    in members_10_to_16
                )
            )

            member_1994 = (
                family.get_member_for_year(
                    1994
                )
            )

            member_1995 = (
                family.get_member_for_year(
                    1995
                )
            )

            member_1996 = (
                family.get_member_for_year(
                    1996
                )
            )

            print(
                "1994:",
                member_1994.name
                if member_1994
                else None
            )

            print(
                "1995:",
                member_1995.name
                if member_1995
                else None
            )

            print(
                "1996:",
                member_1996.name
                if member_1996
                else None
            )

if __name__ == "__main__":
    main()