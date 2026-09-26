import re
from dataclasses import dataclass

from hrs.waves import (
    get_year_for_wave,
    get_years_for_wave,
    is_valid_wave,
)


@dataclass(frozen=True)
class ParsedHRSVariable:
    name: str

    role: str | None

    wave: int | None

    year: int | None

    years: tuple[int, ...] | None

    base_name: str | None

    variable_scope: str

    is_wave_specific: bool


# ---------------------------------------------------------
# Standard RAND HRS naming conventions
#
# Examples:
#
# R15MSTAT
# S1BMONTH
# H15ANYFIN
#
# Group 1 = R / S / H
# Group 2 = wave number
# Group 3 = variable stem
# ---------------------------------------------------------

WAVE_VARIABLE_PATTERN = re.compile(
    r"^([RSH])(\d{1,2})([A-Z].*)$",
    re.IGNORECASE,
)


# ---------------------------------------------------------
# Non-wave-specific variables
#
# Examples:
#
# RAGENDER
# RABYEAR
#
# A = all / not specific to one wave
# ---------------------------------------------------------

ALL_WAVE_VARIABLE_PATTERN = re.compile(
    r"^([RSH])A([A-Z].*)$",
    re.IGNORECASE,
)


# ---------------------------------------------------------
# Exit Interview variables
#
# Example:
#
# REMSTAT
#
# E = Exit Interview
# ---------------------------------------------------------

EXIT_VARIABLE_PATTERN = re.compile(
    r"^([RSH])E([A-Z].*)$",
    re.IGNORECASE,
)


# ---------------------------------------------------------
# Interview-wave indicators
#
# Examples:
#
# INW1
# INW15
# INW16
# ---------------------------------------------------------

INW_PATTERN = re.compile(
    r"^INW(\d{1,2})$",
    re.IGNORECASE,
)


ROLE_MAP = {
    "R": "respondent",
    "S": "spouse",
    "H": "household",
}

SPECIAL_VARIABLES = {
    "HHIDPN": {
        "scope": "identifier",
        "base_name": "HHIDPN",
    },
    "HHID": {
        "scope": "identifier",
        "base_name": "HHID",
    },
    "PN": {
        "scope": "identifier",
        "base_name": "PN",
    },
    "FILEVER": {
        "scope": "file_metadata",
        "base_name": "FILEVER",
    },
}

def _unknown_variable(
    normalized: str,
) -> ParsedHRSVariable:

    return ParsedHRSVariable(
        name=normalized,
        role=None,
        wave=None,
        year=None,
        years=None,
        base_name=None,
        variable_scope="unknown",
        is_wave_specific=False,
    )


def parse_hrs_variable(
    name: str,
) -> ParsedHRSVariable:

    normalized = (
        name
        .strip()
        .upper()
    )

    # -----------------------------------------------------
    # 0. Special RAND HRS variables
    #
    # HHIDPN / HHID / PN = identifiers
    # FILEVER = file version metadata
    # -----------------------------------------------------

    special = SPECIAL_VARIABLES.get(
        normalized
    )

    if special is not None:

        return ParsedHRSVariable(
            name=normalized,
            role=None,
            wave=None,
            year=None,
            years=None,
            base_name=special["base_name"],
            variable_scope=special["scope"],
            is_wave_specific=False,
        )

    # -----------------------------------------------------
    # 1. Standard wave-specific variables
    #
    # R15MSTAT
    # S15CESD
    # H15ANYFIN
    # -----------------------------------------------------

    match = WAVE_VARIABLE_PATTERN.match(
        normalized
    )

    if match is not None:

        role_code = match.group(1)
        wave = int(match.group(2))
        base_name = match.group(3)

        if not is_valid_wave(wave):
            return _unknown_variable(normalized)

        return ParsedHRSVariable(
            name=normalized,
            role=ROLE_MAP[role_code],
            wave=wave,
            year=get_year_for_wave(wave),
            years=get_years_for_wave(wave),
            base_name=base_name,
            variable_scope="wave",
            is_wave_specific=True,
        )

    # -----------------------------------------------------
    # 2. All-wave / wave-independent variables
    #
    # RAGENDER
    # RABYEAR
    # -----------------------------------------------------

    match = ALL_WAVE_VARIABLE_PATTERN.match(
        normalized
    )

    if match is not None:

        role_code = match.group(1)
        base_name = match.group(2)

        return ParsedHRSVariable(
            name=normalized,
            role=ROLE_MAP[role_code],
            wave=None,
            year=None,
            years=None,
            base_name=base_name,
            variable_scope="all",
            is_wave_specific=False,
        )

    # -----------------------------------------------------
    # 3. Exit Interview variables
    #
    # REMSTAT
    # -----------------------------------------------------

    match = EXIT_VARIABLE_PATTERN.match(
        normalized
    )

    if match is not None:

        role_code = match.group(1)
        base_name = match.group(2)

        return ParsedHRSVariable(
            name=normalized,
            role=ROLE_MAP[role_code],
            wave=None,
            year=None,
            years=None,
            base_name=base_name,
            variable_scope="exit",
            is_wave_specific=False,
        )

    # -----------------------------------------------------
    # 4. Interview-wave indicators
    #
    # INW1
    # INW15
    # -----------------------------------------------------

    match = INW_PATTERN.match(
        normalized
    )

    if match is not None:

        wave = int(match.group(1))

        if not is_valid_wave(wave):
            return _unknown_variable(normalized)

        return ParsedHRSVariable(
            name=normalized,
            role="respondent",
            wave=wave,
            year=get_year_for_wave(wave),
            years=get_years_for_wave(wave),
            base_name="INW",
            variable_scope="wave_indicator",
            is_wave_specific=True,
        )

    # -----------------------------------------------------
    # 5. Unknown / special variable
    # -----------------------------------------------------

    return _unknown_variable(
        normalized
    )