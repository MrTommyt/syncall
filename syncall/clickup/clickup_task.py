"""ClickUp task data model."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

from bubop import parse_datetime

if TYPE_CHECKING:
    from syncall.types import ClickUpID, ClickUpRawTask


@dataclass
class ClickUpTask(Mapping):
    """Represent a ClickUp task."""

    name: str
    status: str
    date_created: datetime.datetime
    date_updated: datetime.datetime
    date_closed: datetime.datetime | None = None
    due_date: datetime.datetime | None = None
    description: str | None = None
    id: ClickUpID | None = None

    _key_names: frozenset[str] = frozenset(
        {
            "name",
            "status",
            "date_created",
            "date_updated",
            "date_closed",
            "due_date",
            "description",
            "id",
        },
    )

    def __getitem__(self, key) -> Any:  # noqa: ANN401
        return getattr(self, key)

    def __iter__(self):
        yield from self._key_names

    def __len__(self):
        return len(self._key_names)

    @classmethod
    def from_raw_task(cls, raw_task: ClickUpRawTask) -> ClickUpTask:
        """Create a ClickUpTask from a raw task dictionary."""
        assert "name" in raw_task
        assert "status" in raw_task
        assert "date_created" in raw_task
        assert "date_updated" in raw_task
        assert "id" in raw_task

        name = raw_task["name"]
        
        # Status can be a dict or string
        if isinstance(raw_task["status"], dict):
            status = raw_task["status"].get("status", "")
        else:
            status = raw_task["status"]

        date_created = None
        if raw_task.get("date_created"):
            if isinstance(raw_task["date_created"], datetime.datetime):
                date_created = raw_task["date_created"]
            else:
                # ClickUp uses milliseconds timestamp
                date_created = datetime.datetime.fromtimestamp(
                    int(raw_task["date_created"]) / 1000,
                    tz=datetime.timezone.utc,
                )

        date_updated = None
        if raw_task.get("date_updated"):
            if isinstance(raw_task["date_updated"], datetime.datetime):
                date_updated = raw_task["date_updated"]
            else:
                date_updated = datetime.datetime.fromtimestamp(
                    int(raw_task["date_updated"]) / 1000,
                    tz=datetime.timezone.utc,
                )

        date_closed = None
        if raw_task.get("date_closed"):
            if isinstance(raw_task["date_closed"], datetime.datetime):
                date_closed = raw_task["date_closed"]
            else:
                date_closed = datetime.datetime.fromtimestamp(
                    int(raw_task["date_closed"]) / 1000,
                    tz=datetime.timezone.utc,
                )

        due_date = None
        if raw_task.get("due_date"):
            if isinstance(raw_task["due_date"], datetime.datetime):
                due_date = raw_task["due_date"]
            else:
                due_date = datetime.datetime.fromtimestamp(
                    int(raw_task["due_date"]) / 1000,
                    tz=datetime.timezone.utc,
                )

        description = raw_task.get("description", None) or raw_task.get("content", None)
        task_id = raw_task["id"]

        return ClickUpTask(
            name=name,
            status=status,
            date_created=date_created,
            date_updated=date_updated,
            date_closed=date_closed,
            due_date=due_date,
            description=description,
            id=task_id,
        )

    def to_raw_task(self) -> ClickUpRawTask:
        """Convert the ClickUpTask to a raw task dictionary."""
        raw_task = {
            "name": self.name,
            "status": self.status,
            "id": self.id,
        }

        if self.date_created is not None:
            # Convert to milliseconds timestamp
            raw_task["date_created"] = str(
                int(self.date_created.timestamp() * 1000)
            )
        else:
            raw_task["date_created"] = None

        if self.date_updated is not None:
            raw_task["date_updated"] = str(
                int(self.date_updated.timestamp() * 1000)
            )
        else:
            raw_task["date_updated"] = None

        if self.date_closed is not None:
            raw_task["date_closed"] = str(
                int(self.date_closed.timestamp() * 1000)
            )
        else:
            raw_task["date_closed"] = None

        if self.due_date is not None:
            raw_task["due_date"] = int(self.due_date.timestamp() * 1000)
        else:
            raw_task["due_date"] = None

        if self.description is not None:
            raw_task["description"] = self.description
        else:
            raw_task["description"] = None

        return raw_task
