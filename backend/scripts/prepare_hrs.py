import json
from pathlib import Path

import pyreadstat


# ============================================================
# Paths
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

SOURCE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "randhrs1992_2022v1.sav"
)

MASTER_DIR = (
    PROJECT_ROOT
    / "data"
    / "master"
)

METADATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "metadata"
)

PARQUET_PATH = (
    MASTER_DIR
    / "randhrs1992_2022v1.parquet"
)

METADATA_PATH = (
    METADATA_DIR
    / "hrs_variables.json"
)


# ============================================================
# Main
# ============================================================

def main():

    print("Project root:")
    print(PROJECT_ROOT)

    print("\nLooking for SAV:")
    print(SOURCE)

    if not SOURCE.exists():
        raise FileNotFoundError(
            f"HRS SAV file not found:\n{SOURCE}"
        )

    MASTER_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # 1. Read original SAV
    # --------------------------------------------------------

    print("\nReading HRS SAV...")

    df, meta = pyreadstat.read_sav(
        str(SOURCE),
        apply_value_formats=False,
    )

    print("\nHRS loaded successfully.")

    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    memory_mb = (
        df.memory_usage(deep=True).sum()
        / 1024
        / 1024
    )

    print(
        f"Memory: {memory_mb:.2f} MB"
    )

    # --------------------------------------------------------
    # 2. Save master dataset as Parquet
    # --------------------------------------------------------

    print("\nSaving HRS master Parquet...")

    df.to_parquet(
        PARQUET_PATH,
        engine="pyarrow",
        index=False,
    )

    print("Parquet saved:")
    print(PARQUET_PATH)

    # --------------------------------------------------------
    # 3. Extract basic variable metadata
    # --------------------------------------------------------

    print("\nExtracting variable metadata...")

    variables = []

    labels = (
        meta.column_names_to_labels
        if meta.column_names_to_labels
        else {}
    )

    for column in df.columns:

        variables.append(
            {
                "name": column,
                "label": labels.get(column),
            }
        )

    METADATA_PATH.write_text(
        json.dumps(
            variables,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Metadata saved:")
    print(METADATA_PATH)

    # --------------------------------------------------------
    # 4. Finished
    # --------------------------------------------------------

    print("\nPreparation complete.")

    print("\nGenerated files:")

    print(
        "Master:",
        PARQUET_PATH,
    )

    print(
        "Metadata:",
        METADATA_PATH,
    )


if __name__ == "__main__":
    main()