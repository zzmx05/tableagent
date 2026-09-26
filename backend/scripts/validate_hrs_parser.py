import json
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from hrs.parser import parse_hrs_variable


METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "metadata"
    / "hrs_variables.json"
)


LABEL_WAVE_PATTERN = re.compile(
    r":\s*W(\d{1,2})\b",
    re.IGNORECASE,
)


def main():

    with METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        variables = json.load(file)

    checked = 0
    matched = 0
    mismatches = []

    for item in variables:

        name = item["name"]

        label = (
            item.get("label")
            or ""
        )

        parsed = parse_hrs_variable(
            name
        )

        # Only validate variables for which the parser
        # has assigned a concrete wave.
        if parsed.wave is None:
            continue

        label_match = LABEL_WAVE_PATTERN.search(
            label
        )

        # Some variables may not expose Wxx in the label.
        # They cannot be independently checked here.
        if label_match is None:
            continue

        label_wave = int(
            label_match.group(1)
        )

        checked += 1

        if parsed.wave == label_wave:

            matched += 1

        else:

            mismatches.append({
                "name": name,
                "parsed_wave": parsed.wave,
                "label_wave": label_wave,
                "label": label,
            })

    print(
        "\n=== HRS PARSER VALIDATION ==="
    )

    print(
        "Total variables:",
        len(variables),
    )

    print(
        "Wave variables checked:",
        checked,
    )

    print(
        "Wave matches:",
        matched,
    )

    print(
        "Wave mismatches:",
        len(mismatches),
    )

    if checked > 0:

        accuracy = (
            matched
            / checked
            * 100
        )

        print(
            f"Wave agreement: "
            f"{accuracy:.4f}%"
        )

    print(
        "\n=== FIRST 50 MISMATCHES ==="
    )

    for item in mismatches[:50]:

        print(
            f"{item['name']:<15}"
            f"parser=W{item['parsed_wave']:<3}"
            f"label=W{item['label_wave']:<3}"
            f"{item['label']}"
        )


if __name__ == "__main__":
    main()