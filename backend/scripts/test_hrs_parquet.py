from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

HRS_PATH = (
    PROJECT_ROOT
    / "data"
    / "master"
    / "randhrs1992_2022v1.parquet"
)


def main():

    print("HRS master:")
    print(HRS_PATH)

    if not HRS_PATH.exists():
        raise FileNotFoundError(
            f"HRS Parquet not found:\n{HRS_PATH}"
        )

    # Only read three columns
    columns = [
        "HHIDPN",
        "R1MSTAT",
        "R1MPART",
    ]

    print("\nLoading columns:")
    print(columns)

    df = pd.read_parquet(
        HRS_PATH,
        columns=columns,
        engine="pyarrow",
    )

    print("\n=== SHAPE ===")
    print(df.shape)

    print("\n=== COLUMNS ===")
    print(df.columns.tolist())

    print("\n=== FIRST 5 ROWS ===")
    print(df.head().to_string())

    memory_mb = (
        df.memory_usage(deep=True).sum()
        / 1024
        / 1024
    )

    print("\n=== MEMORY ===")
    print(f"{memory_mb:.2f} MB")


if __name__ == "__main__":
    main()