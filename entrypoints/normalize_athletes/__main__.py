import csv
import pathlib
import re

import bracket_util
import club_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_SIMPLE_NAME = re.compile(r"^[a-z0-9 ]+$")


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
) -> club_util.Athlete | None:
    athlete_map = athlete_lookup.get(team_normalized)
    if athlete_map is None:
        return None

    name_normalized = _normalize_name(name)
    matched = athlete_map.get(name_normalized)
    if matched is not None:
        return matched

    by_team = custom_athlete_name_map.get(team_normalized, {})
    new_name_normalized = by_team.get(name_normalized)
    if new_name_normalized is None:
        return None

    matched = athlete_map.get(new_name_normalized)
    if matched is None:
        raise RuntimeError(
            "Unexpected failure to match custom name",
            name,
            name_normalized,
            new_name_normalized,
            team_normalized,
        )

    return matched


def main() -> None:
    matches_v2 = _load_matches()
    rosters = club_util.load_rosters()
    athlete_lookup = _prepare_athlete_lookup(rosters)

    custom_athlete_name_map = club_util.load_custom_athlete_name_map()

    t1 = 0
    t2 = 0
    for match_ in matches_v2:
        t1 += 2
        winner_athlete = _lookup_athlete(
            match_.winner,
            match_.winner_team_normalized,
            athlete_lookup,
            custom_athlete_name_map,
        )
        loser_athlete = _lookup_athlete(
            match_.loser,
            match_.loser_team_normalized,
            athlete_lookup,
            custom_athlete_name_map,
        )
        if winner_athlete is not None:
            t2 += 1
        if loser_athlete is not None:
            t2 += 1

    print(f"{t2} / {t1}")
    print(t2 / t1)


if __name__ == "__main__":
    main()


# TODO: Deal with team transfers. For example:
#       - `Annebelle Duller` from `Antioch Predators Wrestling Club` to
#         `Stateline Stingers Wrestling Club`
