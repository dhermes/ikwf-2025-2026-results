import datetime
import re

import pydantic


def to_kebab_case(name: str) -> str:
    # Lowercase
    name = name.lower()

    # Remove special characters
    name = re.sub(r"[.`~!@#$%^&*()=+\[\]{}\\|;:'\",<>/?]", "", name)

    # Replace spaces or underscores with hyphen
    name = re.sub(r"[ _]+", "-", name)

    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)

    # Strip leading/trailing hyphens
    name = name.strip("-")

    return name


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


class Tournament(_ForbidExtra):
    name: str
    start_date: datetime.date | None
    end_date: datetime.date
