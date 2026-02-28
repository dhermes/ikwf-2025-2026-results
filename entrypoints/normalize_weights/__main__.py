import csv
import pathlib
import re

import bracket_util
import trackwrestling
import usabracketing

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_SIMPLE_NAME = re.compile(r"^[a-z0-9 ]+$")
_NULLABLE_KEYS = (
    "Division",
    "Winner (normalized)",
    "Winner USAW Number",
    "Winner IKWF Age",
    "Loser (normalized)",
    "Loser USAW Number",
    "Loser IKWF Age",
)
_IGNORED_KEYS: tuple[tuple[str, str, str, str], ...] = (
    # NOTE: `Harrison Thaler` also showed up in `BAN - 71-78` with a
    #       different weight `78.0`
    (
        "Wilbur Borrero Classic",
        "Harrison Thaler",
        "BAN - 69-77",
        "Barrington Broncos WC",
    ),
    # NOTE: `Greyson Miller` also showed up in `BAN - 71-78` with a
    #       different weight `78.0`
    (
        "Wilbur Borrero Classic",
        "Greyson Miller",
        "BAN - 71-78",
        "McHenry Wrestling Club",
    ),
    # NOTE: `Gavin Allen` also showed up in `INT - 55.7-62` with a
    #       different weight `56.0`
    ("Wilbur Borrero Classic", "Gavin Allen", "TOT - 51-56", "Woodstock Cyclones"),
    # NOTE: `Gunnersyn Schulz` also showed up in `B - INT - 80-86` with a
    #       different higher weight `80.0`
    (
        "Champaign Grappler III",
        "Gunnersyn Schulz",
        "B - INT - 74-81.9",
        "El Paso Gridley Youth Wrestling Club",
    ),
    # NOTE: `Monteen Gray` also showed up in `B - INT - 80-86` with a
    #       different higher weight `80.0`
    ("Champaign Grappler III", "Monteen Gray", "B - INT - 77.9-82.5", "CWC"),
)
# NOTE: Some athletes are double bracketed or have a weigh in that does not
#       make sense, so we ignore some on a per-tournament basis.
_IGNORED_WEIGH_INS: dict[str, list[bracket_util.AthleteWeight]] = {
    "Yorkville Fighting Foxes Invitational": [
        bracket_util.AthleteWeight(
            name="Parker Paul", group="8U", team="Yorkville Wrestling Club", weight=55.5
        )
    ],
}


_MappedAthletes = dict[bracket_util.AthleteWeightKey, bracket_util.AthleteWeight]


def _merge_into_results(
    page: _MappedAthletes, results: _MappedAthletes
) -> _MappedAthletes:
    for key, value in page.items():
        if key in results:
            if results[key] != value:
                raise ValueError(
                    "Unexpected non-matching rows", key, value, results[key]
                )
        else:
            results[key] = value

    return results


def _parse_trackwrestling(
    raw_data_dir: pathlib.Path,
) -> dict[str, _MappedAthletes]:
    by_event: dict[str, _MappedAthletes] = {}

    for date_str, name in trackwrestling.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            as_json = file_obj.read()

        fetched_event = bracket_util.FetchedEvent.model_validate_json(as_json)
        athlete_weights_raw = fetched_event.weights_html

        event_weights: _MappedAthletes = {}

        keys = sorted(athlete_weights_raw.keys())
        ignored_weigh_ins = _IGNORED_WEIGH_INS.get(name)
        for key in keys:
            html = athlete_weights_raw[key]
            page_weights = trackwrestling.parse_athlete_weights(
                html, "trackwrestling", ignored_weigh_ins=ignored_weigh_ins
            )
            event_weights = _merge_into_results(page_weights, event_weights)

        by_event[fetched_event.name] = event_weights

    return by_event


def _parse_trackwrestling_duals(
    raw_data_dir: pathlib.Path,
) -> dict[str, _MappedAthletes]:
    by_event: dict[str, _MappedAthletes] = {}

    for date_str, name in trackwrestling.DUAL_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            as_json = file_obj.read()

        fetched_event = bracket_util.FetchedEvent.model_validate_json(as_json)
        athlete_weights_raw = fetched_event.weights_html

        event_weights: _MappedAthletes = {}

        keys = sorted(athlete_weights_raw.keys())
        for key in keys:
            html = athlete_weights_raw[key]
            page_weights = trackwrestling.parse_athlete_weights(
                html, "trackwrestling_dual"
            )
            event_weights = _merge_into_results(page_weights, event_weights)

        by_event[fetched_event.name] = event_weights

    return by_event


def _parse_usabracketing(
    raw_data_dir: pathlib.Path,
) -> dict[str, _MappedAthletes]:
    by_event: dict[str, _MappedAthletes] = {}

    for date_str, name in usabracketing.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            as_json = file_obj.read()

        fetched_event = bracket_util.FetchedEvent.model_validate_json(as_json)
        athlete_weights_raw = fetched_event.weights_html

        event_weights: _MappedAthletes = {}

        keys = sorted(athlete_weights_raw.keys())
        for key in keys:
            html = athlete_weights_raw[key]
            page_weights = usabracketing.parse_athlete_weights(html)
            event_weights = _merge_into_results(page_weights, event_weights)

        by_event[fetched_event.name] = event_weights

    return by_event


def _parse_usabracketing_duals(
    raw_data_dir: pathlib.Path,
) -> dict[str, _MappedAthletes]:
    by_event: dict[str, _MappedAthletes] = {}

    for date_str, name in usabracketing.DUAL_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            as_json = file_obj.read()

        fetched_event = bracket_util.FetchedEvent.model_validate_json(as_json)
        athlete_weights_raw = fetched_event.weights_html

        event_weights: _MappedAthletes = {}

        keys = sorted(athlete_weights_raw.keys())
        for key in keys:
            html = athlete_weights_raw[key]
            page_weights = usabracketing.parse_athlete_weights(html)
            event_weights = _merge_into_results(page_weights, event_weights)

        by_event[fetched_event.name] = event_weights

    return by_event


def _parse_all_weights() -> dict[str, _MappedAthletes]:
    raw_data_dir = _ROOT / "_raw-data"
    by_event = _parse_trackwrestling(raw_data_dir)
    by_event.update(_parse_trackwrestling_duals(raw_data_dir))
    by_event.update(_parse_usabracketing(raw_data_dir))
    by_event.update(_parse_usabracketing_duals(raw_data_dir))
    return by_event


def _load_matches() -> list[bracket_util.MatchV3]:
    input_file = _ROOT / "_parsed-data" / "all-matches-03.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        for key in _NULLABLE_KEYS:
            if row[key] == "":
                row[key] = None

    matches_root = bracket_util.MatchesV3.model_validate(rows)
    return matches_root.root


def _normalize_name(name: str) -> str:
    case_insensitive = name.lower()

    parts = case_insensitive.split()
    whitespace_normalized = " ".join(parts)

    without_punctuation = whitespace_normalized.replace("\xa0", " ")
    without_punctuation = without_punctuation.replace("'", "")
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
    without_punctuation = without_punctuation.replace("benny/rich", "rich")
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


def _lookup_athlete(
    event_name: str,
    name: str,
    bracket: str,
    team: str,
    mapped_athletes: _MappedAthletes,
) -> float | None:
    # Boys Intermediate 74-81.9
    # El Paso Gridley Youth Wrestling Club
    if name == "" and team == "":
        return None

    team = team.strip()  # Normalize
    normalized_name = _normalize_name(name)

    matches: list[bracket_util.AthleteWeightKey] = []
    for key in mapped_athletes:
        ignore_check = (event_name,) + key
        if ignore_check in _IGNORED_KEYS:
            continue

        key_name, _, key_team = key
        if _normalize_name(key_name) != normalized_name:
            continue
        if not ((team == "Unattached" and key_team == "") or (key_team == team)):
            continue
        matches.append(key)

    if len(matches) > 1:
        # NOTE: Some kids are cross-bracketed but have the same weight in all
        #       brackets
        all_weights = set(mapped_athletes[key].weight for key in matches)
        if len(all_weights) == 1:
            return list(all_weights)[0]

    if len(matches) > 1:
        matches = [
            (key_name, key_group, key_team)
            for key_name, key_group, key_team in matches
            if bracket.startswith(key_group)
        ]

    if len(matches) > 1:
        raise RuntimeError(
            "Unexpected number of matching athletes", name, bracket, team, matches
        )

    if len(matches) == 0:
        raise RuntimeError("Could not match athlete", name, bracket, team)

    key = matches[0]
    athlete_weight = mapped_athletes[key]
    return athlete_weight.weight


def main() -> None:
    by_event = _parse_all_weights()
    matches_v3 = _load_matches()

    matches_v4: list[bracket_util.MatchV4] = []
    for match_ in matches_v3:
        mapped_athletes = by_event.get(match_.event_name)
        if mapped_athletes is None:
            raise RuntimeError("Event not found", match_.event_name)

        winner_weight = _lookup_athlete(
            match_.event_name,
            match_.winner,
            match_.bracket,
            match_.winner_team,
            mapped_athletes,
        )
        loser_weight = _lookup_athlete(
            match_.event_name,
            match_.loser,
            match_.bracket,
            match_.loser_team,
            mapped_athletes,
        )

        matches_v4.append(
            bracket_util.MatchV4.from_v3(match_, winner_weight, loser_weight)
        )

    matches_file_v4 = _ROOT / "_parsed-data" / "all-matches-04.csv"
    with open(matches_file_v4, "w") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=bracket_util.CSV_FIELD_NAMES_V4)
        writer.writeheader()
        for match_ in matches_v4:
            writer.writerow(match_.model_dump(mode="json", by_alias=True))


if __name__ == "__main__":
    main()
