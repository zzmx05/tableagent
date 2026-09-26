from dataclasses import dataclass

from hrs.catalog import HRSVariableCatalog
from hrs.parser import parse_hrs_variable


@dataclass(frozen=True)
class HRSVariableFamilyMember:
    name: str
    role: str
    wave: int
    years: tuple[int, ...]
    base_name: str
    label: str | None


@dataclass(frozen=True)
class HRSVariableFamily:
    role: str
    base_name: str
    members: tuple[HRSVariableFamilyMember, ...]

    @property
    def wave_count(self) -> int:
        return len({
            member.wave
            for member in self.members
        })

    @property
    def waves(self) -> tuple[int, ...]:
        return tuple(
            sorted({
                member.wave
                for member in self.members
            })
        )

    @property
    def variable_names(self) -> tuple[str, ...]:
        return tuple(
            member.name
            for member in self.members
        )

    # ========================================================
    # Member lookup
    # ========================================================

    def get_member_for_wave(
        self,
        wave: int,
    ) -> HRSVariableFamilyMember | None:
        """
        Return the variable belonging to a specific HRS wave.

        Example:
        respondent:MSTAT + wave 15
        -> R15MSTAT
        """

        for member in self.members:

            if member.wave == wave:
                return member

        return None

    def get_members_for_waves(
        self,
        waves: list[int] | tuple[int, ...],
    ) -> tuple[HRSVariableFamilyMember, ...]:
        """
        Return all members belonging to the requested waves.

        Missing waves are simply omitted.
        """

        wave_set = set(waves)

        return tuple(
            member
            for member in self.members
            if member.wave in wave_set
        )

    def get_member_for_year(
        self,
        year: int,
    ) -> HRSVariableFamilyMember | None:
        """
        Return the family member associated with a survey year.

        Important:
        Wave 2 -> 1993, 1994
        Wave 3 -> 1995, 1996

        Therefore year lookup must use member.years rather
        than assuming one year per wave.
        """

        for member in self.members:

            if year in member.years:
                return member

        return None


class HRSVariableFamilyIndex:

    def __init__(
        self,
        catalog: HRSVariableCatalog,
    ):
        self.catalog = catalog

        self._families = (
            self._build_families()
        )

    def _build_families(
        self,
    ) -> dict[
        tuple[str, str],
        HRSVariableFamily,
    ]:

        grouped = {}

        for variable in self.catalog.variables:

            name = variable["name"]

            parsed = parse_hrs_variable(
                name
            )

            # Only normal wave-specific variables belong
            # to longitudinal variable families.
            #
            # Do not mix:
            # all / exit / identifier / file metadata / INW

            if (
                parsed.variable_scope != "wave"
                or parsed.role is None
                or parsed.wave is None
                or parsed.years is None
                or parsed.base_name is None
            ):
                continue

            key = (
                parsed.role,
                parsed.base_name,
            )

            member = HRSVariableFamilyMember(
                name=name,
                role=parsed.role,
                wave=parsed.wave,
                years=parsed.years,
                base_name=parsed.base_name,
                label=variable.get("label"),
            )

            grouped.setdefault(
                key,
                [],
            ).append(member)

        families = {}

        for key, members in grouped.items():

            sorted_members = tuple(
                sorted(
                    members,
                    key=lambda item: (
                        item.wave,
                        item.name,
                    ),
                )
            )

            role, base_name = key

            families[key] = HRSVariableFamily(
                role=role,
                base_name=base_name,
                members=sorted_members,
            )

        return families

    @property
    def family_count(self) -> int:
        return len(self._families)

    @property
    def families(
        self,
    ) -> tuple[HRSVariableFamily, ...]:

        return tuple(
            self._families.values()
        )

    def get_family(
        self,
        role: str,
        base_name: str,
    ) -> HRSVariableFamily | None:

        key = (
            role.lower(),
            base_name.upper(),
        )

        return self._families.get(
            key
        )

    def get_family_for_variable(
        self,
        variable_name: str,
    ) -> HRSVariableFamily | None:

        parsed = parse_hrs_variable(
            variable_name
        )

        if (
            parsed.variable_scope != "wave"
            or parsed.role is None
            or parsed.base_name is None
        ):
            return None

        return self.get_family(
            role=parsed.role,
            base_name=parsed.base_name,
        )