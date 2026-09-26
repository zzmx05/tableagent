import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from hrs.waves import (
    HRS_WAVES,
    get_year_for_wave,
    get_wave_for_year,
    is_valid_wave,
    is_valid_year,
)


def main():

    print(
        "\n=== HRS WAVES ==="
    )

    for item in HRS_WAVES:

        print(
            f"Wave {item.wave:<2}"
            f" -> {item.year}"
        )

    print(
        "\n=== LOOKUP TEST ==="
    )

    print(
        "Wave 1:",
        get_year_for_wave(1),
    )

    print(
        "Wave 15:",
        get_year_for_wave(15),
    )

    print(
        "Wave 16:",
        get_year_for_wave(16),
    )

    print(
        "2020:",
        get_wave_for_year(2020),
    )

    print(
        "2022:",
        get_wave_for_year(2022),
    )

    print(
        "\n=== INVALID TEST ==="
    )

    print(
        "Wave 99:",
        get_year_for_wave(99),
    )

    print(
        "Year 2021:",
        get_wave_for_year(2021),
    )

    print(
        "Valid wave 15:",
        is_valid_wave(15),
    )

    print(
        "Valid year 2020:",
        is_valid_year(2020),
    )


if __name__ == "__main__":
    main()