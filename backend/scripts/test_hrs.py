from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

HRS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "randhrs1992_2022v1.pkl"
)


def main():
    print("Loading:")
    print(HRS_PATH)

    df = pd.read_pickle(HRS_PATH)

    print("\n=== HRS DATASET ===")
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    print("\n=== FIRST 20 COLUMNS ===")

    for column in df.columns[:20]:
        print(column)

    print("\n=== FIRST 5 ROWS ===")
    print(
        df.iloc[:5, :10].to_string()
    )

    print("\n=== MEMORY ===")

    memory_mb = (
        df.memory_usage(deep=True).sum()
        / 1024
        / 1024
    )

    print(
        f"{memory_mb:.2f} MB"
    )


if __name__ == "__main__":
    main()