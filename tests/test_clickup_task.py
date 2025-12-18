"""Test ClickUp task model."""

from __future__ import annotations

import datetime
from typing import Any, ClassVar

import pytest
from syncall.clickup.clickup_task import ClickUpTask

from .generic_test_case import GenericTestCase


class TestClickUpTask(GenericTestCase):
    """Test ClickUpTask."""

    BASE_VALID_RAW_TASK: ClassVar[dict[str, Any]] = {
        "id": "abc123",
        "name": "First ClickUp Task",
        "status": "open",
        "date_created": "1657484520000",
        "date_updated": "1657484580000",
        "date_closed": None,
        "due_date": None,
        "description": None,
    }

    def test_from_raw(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()
        clickup_task = ClickUpTask.from_raw_task(valid_raw_task)

        assert clickup_task["id"] == valid_raw_task["id"]
        assert clickup_task["name"] == valid_raw_task["name"]
        assert clickup_task["status"] == valid_raw_task["status"]

    def test_from_raw_task_asserts_keys(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()

        ClickUpTask.from_raw_task(valid_raw_task)

        for key in ["id", "name", "status", "date_created", "date_updated"]:
            copy = valid_raw_task.copy()
            copy.pop(key, None)

            with pytest.raises(AssertionError):
                ClickUpTask.from_raw_task(copy)

    def test_from_raw_task_parses_datetime_fields(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()

        clickup_task = ClickUpTask.from_raw_task(valid_raw_task)

        for key in ["date_created", "date_updated"]:
            assert isinstance(clickup_task[key], datetime.datetime)

        for key in ["date_closed", "due_date"]:
            assert clickup_task[key] is None
            valid_raw_task[key] = "1657484700000"
            clickup_task = ClickUpTask.from_raw_task(valid_raw_task)
            assert isinstance(clickup_task[key], datetime.datetime)

    def test_from_raw_task_handles_status_dict(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()
        valid_raw_task["status"] = {"status": "closed", "color": "#d3d3d3"}
        
        clickup_task = ClickUpTask.from_raw_task(valid_raw_task)
        assert clickup_task["status"] == "closed"

    def test_to_raw_task(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()
        clickup_task = ClickUpTask.from_raw_task(valid_raw_task)
        raw_task = clickup_task.to_raw_task()

        assert raw_task["id"] == clickup_task["id"]
        assert raw_task["name"] == clickup_task["name"]
        assert raw_task["status"] == clickup_task["status"]

        for key in ["date_created", "date_updated"]:
            assert raw_task[key] is not None

        for key in ["date_closed", "due_date"]:
            assert raw_task[key] is None

            valid_raw_task[key] = "1657484700000"

            clickup_task = ClickUpTask.from_raw_task(valid_raw_task)

            raw_task = clickup_task.to_raw_task()
            assert raw_task[key] is not None
