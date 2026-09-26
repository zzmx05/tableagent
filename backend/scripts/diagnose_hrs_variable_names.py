import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from hrs.parser import (
    parse_hrs_variable,
)


METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "hrs_variables.json"
)


def main():

    with METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        variables = json.load(file)

    parsed_variables = []
    unparsed_variables = []
    unparsed_prefix_counts = {}
    scope_counts = {}

    role_counts = {
        "respondent": 0,
        "spouse": 0,
        "household": 0,
    }

    wave_counts = {}

    for item in variables:

        name = item["name"]

        parsed = (
            parse_hrs_variable(
                name
            )
        )

        # --------------------------------------------------------
        # Count variable scopes
        # --------------------------------------------------------

        scope_counts[
            parsed.variable_scope
        ] = (
            scope_counts.get(
                parsed.variable_scope,
                0,
            )
            + 1
        )


        # --------------------------------------------------------
        # Successfully parsed variable
        # --------------------------------------------------------

        if parsed.variable_scope != "unknown":

            parsed_variables.append(
                name
            )

            if parsed.role is not None:

                role_counts[
                    parsed.role
                ] = (
                    role_counts.get(
                        parsed.role,
                        0,
                    )
                    + 1
                )

            if parsed.wave is not None:

                wave_counts[
                    parsed.wave
                ] = (
                    wave_counts.get(
                        parsed.wave,
                        0,
                    )
                    + 1
                )


        # --------------------------------------------------------
        # Truly unknown variable
        # --------------------------------------------------------

        else:

            unparsed_variables.append({
                "name": name,
                "label": item.get("label"),
            })

            prefix = (
                name[:2]
                if len(name) >= 2
                else name
            )

            unparsed_prefix_counts[
                prefix
            ] = (
                unparsed_prefix_counts.get(
                    prefix,
                    0,
                )
                + 1
            )
    print(
        "\n=== HRS VARIABLE NAME DIAGNOSTIC ==="
    )

    print(
        "Total:",
        len(variables),
    )

    print(
        "Successfully parsed:",
        len(parsed_variables),
    )

    print(
        "Unparsed:",
        len(unparsed_variables),
    )

    print(
        "\n=== VARIABLE SCOPE COUNTS ==="
    )

    for scope, count in sorted(
        scope_counts.items()
    ):

        print(
            f"{scope:<20} {count}"
        )

    print(
        "\n=== ROLE COUNTS ==="
    )

    print(role_counts)

    print(
        "\n=== WAVE COUNTS ==="
    )

    for wave in sorted(
        wave_counts
    ):

        print(
            f"Wave {wave}: "
            f"{wave_counts[wave]}"
        )

    print(
        "\n=== UNPARSED PREFIX COUNTS ==="
    )

    sorted_prefixes = sorted(
        unparsed_prefix_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    for prefix, count in sorted_prefixes[:30]:

        print(
            f"{prefix:<5} {count}"
        )

    print(
        "\n=== FIRST 100 UNPARSED ==="
    )

    for item in (
        unparsed_variables[:100]
    ):

        print(
            f"{item['name']:<15}"
            f"{item.get('label')}"
        )


if __name__ == "__main__":
    main()