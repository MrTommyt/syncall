"""ClickUp-Taskwarrior conversion utilities."""

import datetime

import dateutil
from bubop import parse_datetime

from syncall.clickup.clickup_task import ClickUpTask
from syncall.types import TwItem


def convert_tw_to_clickup(tw_item: TwItem) -> ClickUpTask:
    """Convert a Taskwarrior item to a ClickUp task.
    
    Args:
        tw_item: The Taskwarrior item to convert
        
    Returns:
        A ClickUpTask object
    """
    # Extract Taskwarrior fields
    tw_description = tw_item["description"]
    tw_due = tw_item.get("due")
    tw_end = tw_item.get("end")
    tw_entry = tw_item["entry"]
    tw_modified = tw_item["modified"]
    tw_status = tw_item["status"]

    # Declare ClickUp fields
    cu_name = None
    cu_status = "open"
    cu_date_created = None
    cu_date_updated = None
    cu_date_closed = None
    cu_due_date = None
    cu_description = None

    # Convert Taskwarrior fields to ClickUp fields
    cu_name = tw_description

    # Convert status
    if tw_status == "completed":
        cu_status = "closed"
        if tw_end is not None:
            if isinstance(tw_end, datetime.datetime):
                cu_date_closed = tw_end
            else:
                cu_date_closed = parse_datetime(tw_end)
    elif tw_status == "deleted":
        cu_status = "closed"
    else:
        cu_status = "open"

    # Convert dates
    if not isinstance(tw_entry, datetime.datetime):
        cu_date_created = parse_datetime(tw_entry)
    else:
        cu_date_created = tw_entry

    if isinstance(tw_modified, datetime.datetime):
        cu_date_updated = tw_modified
    else:
        cu_date_updated = parse_datetime(tw_modified)

    if tw_due is not None:
        cu_due_date = (
            tw_due if isinstance(tw_due, datetime.datetime) else parse_datetime(tw_due)
        )

    # Build ClickUp task
    return ClickUpTask(
        name=cu_name,
        status=cu_status,
        date_created=cu_date_created,
        date_updated=cu_date_updated,
        date_closed=cu_date_closed,
        due_date=cu_due_date,
        description=cu_description,
    )


def convert_clickup_to_tw(clickup_task: ClickUpTask) -> TwItem:
    """Convert a ClickUp task to a Taskwarrior item.
    
    Args:
        clickup_task: The ClickUp task to convert
        
    Returns:
        A Taskwarrior item dictionary
    """
    # Extract ClickUp fields
    cu_name = clickup_task["name"]
    cu_status = clickup_task["status"]
    cu_date_created = clickup_task["date_created"]
    cu_date_updated = clickup_task["date_updated"]
    cu_date_closed = clickup_task["date_closed"]
    cu_due_date = clickup_task["due_date"]
    cu_description = clickup_task["description"]

    # Declare Taskwarrior fields
    tw_description = None
    tw_status = "pending"
    tw_entry = None
    tw_modified = None
    tw_end = None
    tw_due = None

    # Convert ClickUp fields to Taskwarrior fields
    tw_description = cu_name

    # Convert status
    if cu_status and cu_status.lower() in ["closed", "complete", "completed"]:
        tw_status = "completed"
        if cu_date_closed is not None:
            if isinstance(cu_date_closed, datetime.datetime):
                tw_end = cu_date_closed
            else:
                tw_end = parse_datetime(cu_date_closed)
    else:
        tw_status = "pending"

    # Convert dates
    if isinstance(cu_date_created, datetime.datetime):
        tw_entry = cu_date_created
    else:
        tw_entry = parse_datetime(cu_date_created) if cu_date_created else None

    if cu_date_updated is not None:
        if isinstance(cu_date_updated, datetime.datetime):
            tw_modified = cu_date_updated
        else:
            tw_modified = parse_datetime(cu_date_updated)

    if cu_due_date is not None:
        if isinstance(cu_due_date, datetime.datetime):
            tw_due = cu_due_date
        else:
            tw_due = parse_datetime(cu_due_date)

    # Build Taskwarrior item
    tw_task = {
        "description": tw_description,
        "status": tw_status,
        "entry": tw_entry,
        "modified": tw_modified,
        "due": None,
        "end": tw_end,
    }

    if tw_due is not None:
        tw_task["due"] = tw_due

    if tw_modified is not None:
        tw_task["modified"] = tw_modified

    return tw_task
