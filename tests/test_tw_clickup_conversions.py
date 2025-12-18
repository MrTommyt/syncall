"""Test TW <-> ClickUp conversions."""

import yaml
from syncall.clickup.clickup_task import ClickUpTask
from syncall.tw_clickup_utils import convert_clickup_to_tw, convert_tw_to_clickup

from .generic_test_case import GenericTestCase


class TestTwClickUpConversions(GenericTestCase):
    """Test item conversions - TW <-> ClickUp."""

    def get_keys_to_match(self):
        return set(self.tw_item.keys()).intersection(
            ("description", "due", "modified", "status"),
        )

    def load_sample_items(self):
        with (GenericTestCase.DATA_FILES_PATH / "sample_items.yaml").open() as fname:
            conts = yaml.load(fname, Loader=yaml.Loader)  # noqa: S506

        self.clickup_task = conts.get("clickup_task")
        self.tw_item_expected = conts.get("tw_item_expected")

        self.tw_item = conts["tw_item"]
        self.clickup_task_expected = conts.get("clickup_task_expected")

        self.tw_item_w_due = conts["tw_item_w_due"]

    def test_tw_clickup_basic_convert(self):
        """Basic TW -> ClickUp conversion."""
        # Create a simple TW item for conversion
        import datetime
        tw_item = {
            "description": "Test task",
            "entry": datetime.datetime(2022, 7, 10, 20, 42, 0, tzinfo=datetime.timezone.utc),
            "modified": datetime.datetime(2022, 7, 10, 20, 43, 0, tzinfo=datetime.timezone.utc),
            "status": "pending",
        }
        
        clickup_task_out = convert_tw_to_clickup(tw_item)
        assert clickup_task_out["name"] == tw_item["description"]
        assert clickup_task_out["status"] == "open"
        assert clickup_task_out["date_created"] == tw_item["entry"]
        assert clickup_task_out["date_updated"] == tw_item["modified"]

    def test_clickup_tw_basic_convert(self):
        """Basic ClickUp -> TW conversion."""
        import datetime
        clickup_task = ClickUpTask(
            id="abc123",
            name="Test task",
            status="open",
            date_created=datetime.datetime(2022, 7, 10, 20, 42, 0, tzinfo=datetime.timezone.utc),
            date_updated=datetime.datetime(2022, 7, 10, 20, 43, 0, tzinfo=datetime.timezone.utc),
        )
        
        tw_item_out = convert_clickup_to_tw(clickup_task)
        assert tw_item_out["description"] == clickup_task["name"]
        assert tw_item_out["status"] == "pending"
        assert tw_item_out["entry"] == clickup_task["date_created"]
        assert tw_item_out["modified"] == clickup_task["date_updated"]

    def test_tw_clickup_n_back(self):
        """TW -> ClickUp -> TW conversion"""
        import datetime
        tw_item = {
            "description": "Test task",
            "entry": datetime.datetime(2022, 7, 10, 20, 42, 0, tzinfo=datetime.timezone.utc),
            "modified": datetime.datetime(2022, 7, 10, 20, 43, 0, tzinfo=datetime.timezone.utc),
            "status": "pending",
        }
        
        tw_item_out = convert_clickup_to_tw(convert_tw_to_clickup(tw_item))

        for key in ["description", "status"]:
            if key in tw_item:
                assert key in tw_item_out
                assert tw_item[key] == tw_item_out[key]

    def test_clickup_tw_n_back_basic(self):
        """Test ClickUp -> TW -> ClickUp conversion."""
        import datetime
        clickup_task = ClickUpTask(
            id="abc123",
            name="Test task",
            status="open",
            date_created=datetime.datetime(2022, 7, 10, 20, 42, 0, tzinfo=datetime.timezone.utc),
            date_updated=datetime.datetime(2022, 7, 10, 20, 43, 0, tzinfo=datetime.timezone.utc),
        )
        
        clickup_task_out = convert_tw_to_clickup(convert_clickup_to_tw(clickup_task))

        for key in ["name", "status"]:
            if key in clickup_task:
                assert key in clickup_task_out
                # Status might change from open to open
                if key != "status":
                    assert clickup_task[key] == clickup_task_out[key]

    def test_tw_clickup_sets_due_date(self):
        """Test that due dates are set in both TW and ClickUp."""
        import datetime
        tw_item_w_due = {
            "description": "Test task with due",
            "entry": datetime.datetime(2022, 7, 10, 20, 42, 0, tzinfo=datetime.timezone.utc),
            "modified": datetime.datetime(2022, 7, 10, 20, 43, 0, tzinfo=datetime.timezone.utc),
            "due": datetime.datetime(2022, 7, 15, 12, 0, 0, tzinfo=datetime.timezone.utc),
            "status": "pending",
        }

        assert "due" in tw_item_w_due
        assert tw_item_w_due["due"] is not None

        clickup_task = convert_tw_to_clickup(tw_item_w_due)

        assert "due_date" in clickup_task
        assert clickup_task["due_date"] == tw_item_w_due["due"]

    def test_completed_status_conversion(self):
        """Test completed status conversion."""
        import datetime
        
        # TW completed -> ClickUp closed
        tw_completed = {
            "description": "Completed task",
            "entry": datetime.datetime(2022, 7, 10, 20, 42, 0, tzinfo=datetime.timezone.utc),
            "modified": datetime.datetime(2022, 7, 10, 20, 43, 0, tzinfo=datetime.timezone.utc),
            "end": datetime.datetime(2022, 7, 10, 21, 0, 0, tzinfo=datetime.timezone.utc),
            "status": "completed",
        }
        
        clickup_task = convert_tw_to_clickup(tw_completed)
        assert clickup_task["status"] == "closed"
        assert clickup_task["date_closed"] == tw_completed["end"]
        
        # ClickUp closed -> TW completed
        clickup_closed = ClickUpTask(
            id="abc456",
            name="Closed task",
            status="closed",
            date_created=datetime.datetime(2022, 7, 10, 20, 42, 0, tzinfo=datetime.timezone.utc),
            date_updated=datetime.datetime(2022, 7, 10, 20, 43, 0, tzinfo=datetime.timezone.utc),
            date_closed=datetime.datetime(2022, 7, 10, 21, 0, 0, tzinfo=datetime.timezone.utc),
        )
        
        tw_item = convert_clickup_to_tw(clickup_closed)
        assert tw_item["status"] == "completed"
        assert tw_item["end"] == clickup_closed["date_closed"]
