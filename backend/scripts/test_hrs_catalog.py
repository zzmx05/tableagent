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


METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "hrs_variables.json"
)


def print_results(
    query: str,
    results: list[dict],
):

    print(
        f"\n=== SEARCH: {query} ==="
    )

    print(
        "Matches:",
        len(results),
    )

    for item in results:

        print(
            f"{item['name']:<15}"
            f"score={item['score']:<4}"
            f"{item.get('label')}"
        )


def main():

    catalog = HRSVariableCatalog(
        METADATA_PATH
    )

    print(
        "\n=== HRS VARIABLE CATALOG ==="
    )

    print(
        "Variables:",
        catalog.variable_count,
    )

    # --------------------------------------------------------
    # Exact lookup
    # --------------------------------------------------------

    print(
        "\n=== EXACT LOOKUP ==="
    )

    variable = catalog.get(
        "R1MSTAT"
    )

    print(variable)

    print(
        "Has R1MSTAT:",
        catalog.has_variable(
            "R1MSTAT"
        ),
    )

    print(
        "Has FAKE_VARIABLE:",
        catalog.has_variable(
            "FAKE_VARIABLE"
        ),
    )

    # --------------------------------------------------------
    # Search tests
    # --------------------------------------------------------

    queries = [
        "marital status",
        "partnered",
        "birth year",
        "spouse",
        "health",
    ]

    for query in queries:

        results = catalog.search(
            query,
            limit=10,
        )

        print_results(
            query,
            results,
        )
    # --------------------------------------------------------
    # Catalog / Repository consistency
    # --------------------------------------------------------

    from hrs.repository import HRSRepository

    HRS_PATH = (
        PROJECT_ROOT
        / "data"
        / "master"
        / "randhrs1992_2022v1.parquet"
    )

    repo = HRSRepository(
        HRS_PATH
    )

    catalog_names = {
        item["name"]
        for item in catalog.variables
    }

    repository_names = set(
        repo.columns
    )

    only_in_catalog = (
        catalog_names
        - repository_names
    )

    only_in_repository = (
        repository_names
        - catalog_names
    )

    print(
        "\n=== CATALOG / REPOSITORY CONSISTENCY ==="
    )

    print(
        "Only in catalog:",
        len(only_in_catalog),
    )

    print(
        "Only in repository:",
        len(only_in_repository),
    )

if __name__ == "__main__":
    main()