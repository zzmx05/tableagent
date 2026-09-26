from dataclasses import dataclass

from hrs.catalog import HRSVariableCatalog
from hrs.families import (
    HRSVariableFamily,
    HRSVariableFamilyIndex,
)


@dataclass(frozen=True)
class HRSSemanticSearchResult:
    role: str
    base_name: str

    score: int
    match_type: str

    representative_name: str
    representative_label: str | None

    wave_count: int
    waves: tuple[int, ...]

    family: HRSVariableFamily


class HRSSemanticSearch:

    def __init__(
        self,
        catalog: HRSVariableCatalog,
        families: HRSVariableFamilyIndex,
    ):
        self.catalog = catalog
        self.families = families

    def search_families(
        self,
        query: str,
        limit: int = 20,
    ) -> list[HRSSemanticSearchResult]:

        normalized = (
            query
            .strip()
            .lower()
        )

        if not normalized:
            return []

        query_words = (
            normalized.split()
        )

        results = []

        for family in self.families.families:

            score = 0
            match_type = ""

            base_name = (
                family.base_name.lower()
            )

            # =================================================
            # 1. Exact base-name match
            # =================================================

            if normalized == base_name:

                score = 100
                match_type = (
                    "exact_base_name"
                )

            # =================================================
            # 2. Query contained in base name
            # =================================================

            elif normalized in base_name:

                score = 80
                match_type = (
                    "base_name"
                )

            # =================================================
            # 3. Search family member labels
            # =================================================

            else:

                best_label_score = 0

                for member in family.members:

                    label = (
                        member.label
                        or ""
                    ).lower()

                    # Exact phrase appears in label
                    if normalized in label:

                        best_label_score = max(
                            best_label_score,
                            70,
                        )

                    # Every query word appears somewhere
                    # in the label
                    elif (
                        query_words
                        and all(
                            word in label
                            for word in query_words
                        )
                    ):

                        best_label_score = max(
                            best_label_score,
                            50,
                        )

                if best_label_score > 0:

                    score = (
                        best_label_score
                    )

                    match_type = "label"

            # =================================================
            # No match
            # =================================================

            if score <= 0:
                continue

            # Family members are already sorted by wave.
            # For now use the latest available member as a
            # representative example for downstream Agent use.
            #
            # This does NOT mean the latest wave is
            # semantically more authoritative.
            representative = (
                family.members[-1]
            )

            results.append(
                HRSSemanticSearchResult(
                    role=family.role,
                    base_name=family.base_name,

                    score=score,
                    match_type=match_type,

                    representative_name=(
                        representative.name
                    ),

                    representative_label=(
                        representative.label
                    ),

                    wave_count=(
                        family.wave_count
                    ),

                    waves=(
                        family.waves
                    ),

                    family=family,
                )
            )

        # =====================================================
        # Ranking
        # =====================================================

        results.sort(
            key=lambda item: (
                -item.score,
                -item.wave_count,
                item.role,
                item.base_name,
            )
        )

        return results[:limit]