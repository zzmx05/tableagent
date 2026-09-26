import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from hrs.repository import HRSRepository


HRS_PATH = (
    PROJECT_ROOT
    / "data"
    / "master"
    / "randhrs1992_2022v1.parquet"
)


def main():

    repo = HRSRepository(
        HRS_PATH
    )

    print(
        "\n=== HRS REPOSITORY ==="
    )

    print(
        "Total columns:",
        repo.column_count,
    )

    print(
        "\nFirst 20 columns:"
    )

    for column in repo.columns[:20]:
        print(column)

    print(
        "\nHas HHIDPN:",
        repo.has_column("HHIDPN"),
    )

    print(
        "Has FAKE_VARIABLE:",
        repo.has_column(
            "FAKE_VARIABLE"
        ),
    )

    # --------------------------------------------------------
    # Extract working data
    # --------------------------------------------------------

    columns = [
        "HHIDPN",
        "R1MSTAT",
        "R1MPART",
    ]

    print(
        "\nExtracting:",
        columns,
    )

    df = repo.extract(
        columns
    )

    print(
        "\n=== WORKING DATA ==="
    )

    print(
        "Shape:",
        df.shape,
    )

    print(
        "\nHead:"
    )

    print(
        df.head().to_string()
    )

    memory_mb = (
        df.memory_usage(
            deep=True
        ).sum()
        / 1024
        / 1024
    )

    print(
        "\nMemory:",
        f"{memory_mb:.2f} MB",
    )



    print(
        "\n=== INVALID COLUMN TEST ==="
    )

    try:

        repo.extract([
            "HHIDPN",
            "FAKE_VARIABLE",
        ])

    except ValueError as error:

        print(
            "Correctly rejected:"
        )

        print(error)

if __name__ == "__main__":
    main()
