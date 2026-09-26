from dataclasses import dataclass


@dataclass(frozen=True)
class HRSWave:
    wave: int
    years: tuple[int, ...]


# ---------------------------------------------------------
# RAND HRS Longitudinal File 1992–2022
#
# Important:
# Wave 2 contains 1993 and 1994 interviews.
# Wave 3 contains 1995 and 1996 interviews.
# From Wave 4 onward, waves correspond to a single
# biennial survey year.
# ---------------------------------------------------------

HRS_WAVES = [
    HRSWave(wave=1, years=(1992,)),
    HRSWave(wave=2, years=(1993, 1994)),
    HRSWave(wave=3, years=(1995, 1996)),
    HRSWave(wave=4, years=(1998,)),
    HRSWave(wave=5, years=(2000,)),
    HRSWave(wave=6, years=(2002,)),
    HRSWave(wave=7, years=(2004,)),
    HRSWave(wave=8, years=(2006,)),
    HRSWave(wave=9, years=(2008,)),
    HRSWave(wave=10, years=(2010,)),
    HRSWave(wave=11, years=(2012,)),
    HRSWave(wave=12, years=(2014,)),
    HRSWave(wave=13, years=(2016,)),
    HRSWave(wave=14, years=(2018,)),
    HRSWave(wave=15, years=(2020,)),
    HRSWave(wave=16, years=(2022,)),
]


# ---------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------

WAVE_TO_YEARS = {
    item.wave: item.years
    for item in HRS_WAVES
}


YEAR_TO_WAVE = {
    year: item.wave
    for item in HRS_WAVES
    for year in item.years
}


# ---------------------------------------------------------
# Public helpers
# ---------------------------------------------------------

def get_years_for_wave(
    wave: int,
) -> tuple[int, ...] | None:
    """
    Return all survey years associated with a RAND HRS wave.
    """
    return WAVE_TO_YEARS.get(wave)


def get_year_for_wave(
    wave: int,
) -> int | None:
    """
    Backward-compatible helper.

    Returns the canonical/latest year associated with the wave.

    Example:
        Wave 2 -> 1994
        Wave 3 -> 1996

    New code that needs the complete mapping should use
    get_years_for_wave().
    """
    years = get_years_for_wave(wave)

    if not years:
        return None

    return years[-1]


def get_wave_for_year(
    year: int,
) -> int | None:
    return YEAR_TO_WAVE.get(year)


def is_valid_wave(
    wave: int,
) -> bool:
    return wave in WAVE_TO_YEARS


def is_valid_year(
    year: int,
) -> bool:
    return year in YEAR_TO_WAVE