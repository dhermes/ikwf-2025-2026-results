import csv
import pathlib
import re

import bracket_util
import club_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_SIMPLE_NAME = re.compile(r"^[a-z0-9 ]+$")
_TOT_SORT_INDEX = 1
_BANTAM_SORT_INDEX = 2
_INTERMEDIATE_SORT_INDEX = 3
_NOVICE_SORT_INDEX = 4
_SENIOR_SORT_INDEX = 5


def _load_matches() -> list[bracket_util.MatchV2]:
    input_file = _ROOT / "_parsed-data" / "all-matches-02.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        if row["Division"] == "":
            row["Division"] = None

    matches_root = bracket_util.MatchesV2.model_validate(rows)
    return matches_root.root


def _normalize_name(name: str) -> str:
    case_insensitive = name.lower()

    parts = case_insensitive.split()
    whitespace_normalized = " ".join(parts)

    without_punctuation = whitespace_normalized.replace("'", "")
    without_punctuation = without_punctuation.replace("\u2019", "")
    without_punctuation = without_punctuation.replace('"', "")
    without_punctuation = without_punctuation.replace(".", "")
    without_punctuation = without_punctuation.replace(",", "")
    without_punctuation = without_punctuation.replace("&", "and")
    without_punctuation = without_punctuation.replace("-", " ")
    without_punctuation = without_punctuation.replace("`", "")
    without_punctuation = without_punctuation.replace("\xe9", "e")
    without_punctuation = without_punctuation.replace("\xf1", "n")
    without_punctuation = without_punctuation.replace("\xed", "i")
    without_punctuation = without_punctuation.replace("\xe1", "a")
    # Very special cases
    without_punctuation = without_punctuation.replace("bassam/sammie", "bassam")
    without_punctuation = without_punctuation.replace("paul/ryland", "paul")
    without_punctuation = without_punctuation.replace("ryland/ paul", "paul")
    without_punctuation = without_punctuation.replace("ryland/paul", "paul")
    without_punctuation = without_punctuation.replace("[kar dee a]", "")
    without_punctuation = without_punctuation.replace("richard/ benny", "richard")
    without_punctuation = without_punctuation.replace("ta?leigha", "taleigha")
    without_punctuation = without_punctuation.replace("o?connor", "oconnor")
    without_punctuation = without_punctuation.replace("tre?lyn", "trelyn")
    without_punctuation = without_punctuation.replace("benny/richard", "richard")
    without_punctuation = without_punctuation.replace("a?mari", "amari")

    without_punctuation = without_punctuation.replace(" (", " ")
    without_punctuation = without_punctuation.replace(") ", " ")
    without_punctuation = without_punctuation.replace(" / ", " ")
    if without_punctuation.startswith("("):
        without_punctuation = without_punctuation[1:]
    if without_punctuation.endswith(")"):
        without_punctuation = without_punctuation[:-1]

    if _SIMPLE_NAME.match(without_punctuation) is None:
        raise RuntimeError("Unhandled name needs normalized", name, without_punctuation)

    parts = without_punctuation.split()
    whitespace_normalized = " ".join(parts)

    return whitespace_normalized


_AthleteLookup = dict[str, dict[str, club_util.Athlete]]


def _prepare_athlete_lookup(
    rosters: list[club_util.ClubInfo],
) -> _AthleteLookup:
    roster_map: _AthleteLookup = {}
    for roster in rosters:
        athlete_map: dict[str, club_util.Athlete] = {}
        for athlete in roster.athletes:
            normalized_name = _normalize_name(athlete.name)
            if normalized_name in athlete_map:
                raise RuntimeError(
                    "Unexpected duplicate",
                    normalized_name,
                    athlete,
                    athlete_map[normalized_name],
                )

            athlete_map[normalized_name] = athlete

        if roster.club_name in roster_map:
            raise RuntimeError("Unexpected duplicate", roster.club_name)

        roster_map[roster.club_name] = athlete_map

    return roster_map


_CustomAthleteNameMap = dict[str, dict[str, str | None]]


def _lookup_athlete(
    name: str,
    team_normalized: str,
    athlete_lookup: _AthleteLookup,
    custom_athlete_name_map: _CustomAthleteNameMap,
) -> tuple[str, club_util.Athlete | None]:
    athlete_map = athlete_lookup.get(team_normalized)
    if athlete_map is None:
        return team_normalized, None

    name_normalized = _normalize_name(name)
    matched = athlete_map.get(name_normalized)
    if matched is not None:
        return team_normalized, matched

    by_team = custom_athlete_name_map.get(team_normalized, {})
    if name_normalized not in by_team:
        raise ValueError(
            "All unmatched athletes should be present in custom athlete name map",
            name,
            name_normalized,
            team_normalized,
        )

    new_name_normalized = by_team[name_normalized]
    if new_name_normalized is None:
        # TODO: Do not allow this branch at all (i.e. fill in all of the missing
        #       mappings)
        return team_normalized, None

    if "::" in new_name_normalized:
        transfer_team, transfer_name = new_name_normalized.split("::")
        return transfer_team, athlete_lookup[transfer_team][transfer_name]

    matched = athlete_map.get(new_name_normalized)
    if matched is None:
        raise RuntimeError(
            "Unexpected failure to match custom name",
            name,
            name_normalized,
            new_name_normalized,
            team_normalized,
        )

    return team_normalized, matched


def _athlete_to_tuple(
    athlete: club_util.Athlete | None,
) -> tuple[str, str, int] | tuple[None, None, None]:
    if athlete is None:
        return None, None, None

    return athlete.name, athlete.usaw_number, athlete.ikwf_age


def _map_age_for_sort(ikwf_age: int) -> int:
    if ikwf_age <= 6:
        return _TOT_SORT_INDEX

    if ikwf_age <= 8:
        return _BANTAM_SORT_INDEX

    if ikwf_age <= 10:
        return _INTERMEDIATE_SORT_INDEX

    if ikwf_age <= 12:
        return _NOVICE_SORT_INDEX

    if ikwf_age <= 14:
        return _SENIOR_SORT_INDEX

    if ikwf_age == 15:
        return _SENIOR_SORT_INDEX

    raise RuntimeError("Unsupported IKWF age", ikwf_age)


def _map_division_for_sort(division: bracket_util.Division) -> int:
    if division in ("tot", "girls_tot"):
        return _TOT_SORT_INDEX

    if division in ("bantam", "girls_bantam"):
        return _BANTAM_SORT_INDEX

    if division in ("intermediate", "girls_intermediate"):
        return _INTERMEDIATE_SORT_INDEX

    if division in ("novice", "girls_novice"):
        return _NOVICE_SORT_INDEX

    if division in ("senior", "girls_senior"):
        return _SENIOR_SORT_INDEX

    raise RuntimeError("Unsuppored division", division)


def _check_age(
    division: bracket_util.Division | None,
    usaw_number: str | None,
    ikwf_age: int | None,
) -> None:
    if ikwf_age is None or division is None:
        return

    age_sort = _map_age_for_sort(ikwf_age)
    division_sort = _map_division_for_sort(division)
    if age_sort > division_sort:
        # raise ValueError("Invalid division for age", usaw_number, division, ikwf_age)
        print(ValueError("Invalid division for age", usaw_number, division, ikwf_age))


def main() -> None:
    matches_v2 = _load_matches()
    rosters = club_util.load_rosters()
    athlete_lookup = _prepare_athlete_lookup(rosters)

    custom_athlete_name_map = club_util.load_custom_athlete_name_map()

    matches_v3: list[bracket_util.MatchV3] = []
    for match_ in matches_v2:
        winner_team_normalized, winner_athlete = _lookup_athlete(
            match_.winner,
            match_.winner_team_normalized,
            athlete_lookup,
            custom_athlete_name_map,
        )
        winner_normalized, winner_usaw_number, winner_ikwf_age = _athlete_to_tuple(
            winner_athlete
        )
        loser_team_normalized, loser_athlete = _lookup_athlete(
            match_.loser,
            match_.loser_team_normalized,
            athlete_lookup,
            custom_athlete_name_map,
        )
        loser_normalized, loser_usaw_number, loser_ikwf_age = _athlete_to_tuple(
            loser_athlete
        )

        _check_age(match_.division, winner_usaw_number, winner_ikwf_age)
        _check_age(match_.division, loser_usaw_number, loser_ikwf_age)

        matches_v3.append(
            bracket_util.MatchV3.from_v2(
                match_,
                winner_team_normalized,
                winner_normalized,
                winner_usaw_number,
                winner_ikwf_age,
                loser_team_normalized,
                loser_normalized,
                loser_usaw_number,
                loser_ikwf_age,
            )
        )

    matches_file_v3 = _ROOT / "_parsed-data" / "all-matches-03.csv"
    with open(matches_file_v3, "w") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=bracket_util.CSV_FIELD_NAMES_V3)
        writer.writeheader()
        for match_ in matches_v3:
            writer.writerow(match_.model_dump(mode="json", by_alias=True))


if __name__ == "__main__":
    main()
