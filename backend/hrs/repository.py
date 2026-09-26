from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


class HRSRepository:
    """
    Read-only access layer for the HRS master dataset.

    Responsibilities:
    - Know which columns exist in the HRS master dataset.
    - Extract selected columns from Parquet.
    - Never modify the master dataset.

    It does NOT handle:
    - versioning
    - rollback
    - data cleaning
    - statistical analysis
    """

    def __init__(
        self,
        data_path: str | Path,
    ):
        self.data_path = Path(data_path)

        if not self.data_path.exists():
            raise FileNotFoundError(
                f"HRS master dataset not found:\n"
                f"{self.data_path}"
            )

        if (
            self.data_path.suffix.lower()
            != ".parquet"
        ):
            raise ValueError(
                "HRS master dataset must "
                "be a Parquet file."
            )

        self._columns = self._load_columns()

    # ========================================================
    # Metadata
    # ========================================================

    def _load_columns(self) -> list[str]:
        """
        Read column names from the Parquet schema
        without loading the full dataset.
        """

        parquet_file = pq.ParquetFile(
            self.data_path
        )

        return (
            parquet_file
            .schema_arrow
            .names
        )

    @property
    def columns(self) -> list[str]:
        """
        Return all available HRS column names.
        """

        return self._columns.copy()

    @property
    def column_count(self) -> int:
        return len(self._columns)

    # ========================================================
    # Validation
    # ========================================================

    def has_column(
        self,
        column: str,
    ) -> bool:

        return column in self._columns

    def validate_columns(
        self,
        columns: list[str],
    ) -> None:

        missing = [
            column
            for column in columns
            if column not in self._columns
        ]

        if missing:
            raise ValueError(
                "Columns not found in HRS master "
                f"dataset: {missing}"
            )

    # ========================================================
    # Data extraction
    # ========================================================

    def extract(
        self,
        columns: list[str],
    ) -> pd.DataFrame:
        """
        Extract selected columns from the HRS
        master dataset.

        Only requested columns are loaded into memory.
        """

        if not columns:
            raise ValueError(
                "At least one column must "
                "be requested."
            )

        # Remove duplicates while preserving order
        unique_columns = list(
            dict.fromkeys(columns)
        )

        self.validate_columns(
            unique_columns
        )

        df = pd.read_parquet(
            self.data_path,
            columns=unique_columns,
            engine="pyarrow",
        )

        return df