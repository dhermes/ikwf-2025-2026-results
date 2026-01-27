import csv
import pathlib

import bracket_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


def main() -> None:
    input_file = _ROOT / "_parsed-data" / "all-matches-01.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        if row["Division"] == "":
            row["Division"] = None

    root = bracket_util.Matches.model_validate(rows)
    print(len(root.root))


if __name__ == "__main__":
    main()
