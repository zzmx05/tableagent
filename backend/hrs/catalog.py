import json
from pathlib import Path
from typing import Any


class HRSVariableCatalog:
    """
    Semantic catalog for HRS variables.

    Responsibilities:
    - Load HRS variable metadata.
    - Find variables by exact name.
    - Search variables by name or label.
    - Return variable descriptions.

    It does NOT read actual HRS respondent data.
    """

    def __init__(
        self,
        metadata_path: str | Path,
    ):
        self.metadata_path = Path(
            metadata_path
        )

        if not self.metadata_path.exists():
            raise FileNotFoundError(
                "HRS variable metadata not found:\n"
                f"{self.metadata_path}"
            )

        self._variables = (
            self._load_metadata()
        )

        self._by_name = {
            item["name"].upper(): item
            for item in self._variables
        }

    # ========================================================
    # Loading
    # ========================================================

    def _load_metadata(
        self,
    ) -> list[dict[str, Any]]:

        with self.metadata_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                "HRS metadata must be a list."
            )

        return data

    # ========================================================
    # Basic information
    # ========================================================

    @property
    def variable_count(
        self,
    ) -> int:

        return len(self._variables)

    @property
    def variables(
        self,
    ) -> list[dict[str, Any]]:

        return [
            item.copy()
            for item in self._variables
        ]

    # ========================================================
    # Exact lookup
    # ========================================================

    def has_variable(
        self,
        name: str,
    ) -> bool:

        return (
            name.upper()
            in self._by_name
        )

    def get(
        self,
        name: str,
    ) -> dict[str, Any] | None:

        item = self._by_name.get(
            name.upper()
        )

        if item is None:
            return None

        return item.copy()

    # ========================================================
    # Search
    # ========================================================

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:

        query = query.strip().lower()

        if not query:
            return []

        matches = []

        for item in self._variables:

            name = (
                item.get("name")
                or ""
            )

            label = (
                item.get("label")
                or ""
            )

            name_lower = name.lower()
            label_lower = label.lower()

            score = 0

            # Exact variable name
            if query == name_lower:
                score = 100

            # Variable name contains query
            elif query in name_lower:
                score = 80

            # Label contains exact phrase
            elif query in label_lower:
                score = 60

            else:
                # All query words appear in label
                words = query.split()

                if (
                    words
                    and all(
                        word in label_lower
                        for word in words
                    )
                ):
                    score = 40

            if score > 0:

                matches.append({
                    **item,
                    "score": score,
                })

        matches.sort(
            key=lambda item: (
                -item["score"],
                item["name"],
            )
        )

        return matches[:limit]