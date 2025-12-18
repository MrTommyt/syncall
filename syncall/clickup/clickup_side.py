"""ClickUp side implementation for syncall."""

from typing import Optional, Sequence

import pyclickup

from syncall.clickup.clickup_task import ClickUpTask
from syncall.sync_side import SyncSide
from syncall.types import ClickUpID


class ClickUpSide(SyncSide):
    """Wrapper class to add/modify/delete ClickUp tasks."""

    def __init__(
        self,
        client: pyclickup.ClickUp,
        list_id: ClickUpID,
        team_id: ClickUpID,
    ):
        """Initialize the ClickUp side.
        
        Args:
            client: The pyclickup client instance
            list_id: The ClickUp list ID to sync tasks with
            team_id: The ClickUp team/workspace ID
        """
        self._client = client
        self._list_id = list_id
        self._team_id = team_id

        super().__init__(name="ClickUp", fullname="ClickUp")

    def start(self):
        """Initialize the ClickUp side."""
        pass

    def finish(self):
        """Clean up the ClickUp side."""
        pass

    def get_all_items(self, **kwargs) -> Sequence[ClickUpTask]:
        """Get all tasks from the ClickUp list.
        
        Returns:
            A sequence of ClickUpTask objects
        """
        del kwargs
        results = []

        # Get tasks from the specified list
        # pyclickup returns tasks with paging
        tasks_response = self._client.get(
            f"list/{self._list_id}/task",
            params={
                "archived": False,
                "include_closed": True,
            }
        )
        
        if "tasks" in tasks_response:
            for task in tasks_response["tasks"]:
                clickup_task = ClickUpTask.from_raw_task(task)
                results.append(clickup_task)

        return results

    def get_item(self, item_id: ClickUpID) -> Optional[ClickUpTask]:
        """Get a single task based on the given ID.

        Args:
            item_id: The ClickUp task ID
            
        Returns:
            None if not found, the task otherwise
        """
        try:
            task_response = self._client.get(f"task/{item_id}")
            return ClickUpTask.from_raw_task(task_response)
        except Exception:
            # Task not found or error occurred
            return None

    def delete_single_item(self, item_id: ClickUpID):
        """Delete a task based on the given ID.
        
        Args:
            item_id: The ClickUp task ID to delete
        """
        # pyclickup doesn't have a delete method, so we use the requests library directly
        import requests
        url = f"{self._client.api_url}task/{item_id}"
        response = requests.delete(url, headers=self._client.headers)
        response.raise_for_status()

    def update_item(self, item_id: ClickUpID, **changes):
        """Update the given task.

        Args:
            item_id: ID of task to update
            changes: Keyword parameters that are to change in the task
        """
        raw_task = ClickUpTask(**changes).to_raw_task()

        # Remove keys that ClickUp doesn't let us change
        raw_task.pop("date_created", None)
        raw_task.pop("date_updated", None)
        raw_task.pop("id", None)

        # Prepare update payload
        update_data = {}
        if "name" in raw_task and raw_task["name"]:
            update_data["name"] = raw_task["name"]
        if "status" in raw_task and raw_task["status"]:
            update_data["status"] = raw_task["status"]
        if "description" in raw_task and raw_task["description"] is not None:
            update_data["description"] = raw_task["description"]
        if "due_date" in raw_task:
            update_data["due_date"] = raw_task["due_date"]

        self._client.put(f"task/{item_id}", data=update_data)

    def add_item(self, item: ClickUpTask) -> ClickUpTask:
        """Add a new task.

        Args:
            item: The task to add
            
        Returns:
            The newly added task
        """
        raw_task = item.to_raw_task()

        # Prepare create payload
        create_data = {
            "name": raw_task["name"],
        }
        
        if raw_task.get("status"):
            create_data["status"] = raw_task["status"]
        if raw_task.get("description"):
            create_data["description"] = raw_task["description"]
        if raw_task.get("due_date"):
            create_data["due_date"] = raw_task["due_date"]

        # Create the task
        response = self._client.post(
            f"list/{self._list_id}/task",
            data=create_data
        )
        
        return ClickUpTask.from_raw_task(response)

    @classmethod
    def id_key(cls) -> str:
        """Key in the dictionary of the task that refers to the ID."""
        return "id"

    @classmethod
    def summary_key(cls) -> str:
        """Key in the dictionary of the task that refers to its summary."""
        return "name"

    @classmethod
    def last_modification_key(cls) -> str:
        """Key in the dictionary of the task that refers to its modification date."""
        return "date_updated"

    @classmethod
    def items_are_identical(
        cls,
        item1: ClickUpTask,
        item2: ClickUpTask,
        ignore_keys: Sequence[str] = [],
    ) -> bool:
        """Determine whether two tasks are identical.

        Args:
            item1: First task to compare
            item2: Second task to compare
            ignore_keys: Keys to ignore during comparison
            
        Returns:
            True if tasks are identical, False otherwise
        """
        compare_keys = ClickUpTask._key_names.copy()

        for key in ignore_keys:
            if key in compare_keys:
                compare_keys.remove(key)

        return SyncSide._items_are_identical(item1, item2, compare_keys)
