"""Taskwarrior <-> ClickUp synchronization script."""

from __future__ import annotations

import sys

import click
import pyclickup
from bubop import (
    check_optional_mutually_exclusive,
    check_required_mutually_exclusive,
    format_dict,
    logger,
    loguru_tqdm_sink,
)

from syncall.app_utils import confirm_before_proceeding, inform_about_app_extras

try:
    from syncall.clickup.clickup_side import ClickUpSide
    from syncall.clickup.utils import list_clickup_lists, list_clickup_teams
    from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide
except ImportError:
    inform_about_app_extras(["clickup", "tw"])


from syncall.aggregator import Aggregator
from syncall.app_utils import (
    app_log_to_syslog,
    cache_or_reuse_cached_combination,
    error_and_exit,
    fetch_app_configuration,
    get_resolution_strategy,
    register_teardown_handler,
)
from syncall.cli import opts_clickup, opts_miscellaneous, opts_tw_filtering
from syncall.tw_clickup_utils import convert_clickup_to_tw, convert_tw_to_clickup


# CLI parsing ---------------------------------------------------------------------------------
@click.command()
@opts_clickup()
@opts_tw_filtering()
@opts_miscellaneous("TW", "ClickUp")
def main(
    clickup_token: str,
    clickup_list_id: str,
    clickup_team_id: str,
    do_list_clickup_teams: bool,
    do_list_clickup_lists: bool,
    tw_filter: str,
    tw_tags: list[str],
    tw_project: str,
    tw_only_modified_last_X_days: str,
    tw_sync_all_tasks: bool,
    prefer_scheduled_date: bool,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    pdb_on_error: bool,
    confirm: bool,
):
    """Synchronize your tasks in ClickUp with filters from Taskwarrior."""
    del prefer_scheduled_date

    loguru_tqdm_sink(verbosity=verbose)
    app_log_to_syslog()
    logger.debug("Initialising...")
    inform_about_config = False

    # cli validation --------------------------------------------------------------------------
    check_optional_mutually_exclusive(combination_name, custom_combination_savename)

    tw_filter_li = [
        t
        for t in [
            tw_filter,
            tw_only_modified_last_X_days,
        ]
        if t
    ]

    combination_of_tw_filters_and_clickup_list = any(
        [
            tw_filter_li,
            tw_tags,
            tw_project,
            tw_sync_all_tasks,
            clickup_list_id,
            clickup_team_id,
        ],
    )
    check_optional_mutually_exclusive(
        combination_name,
        combination_of_tw_filters_and_clickup_list,
    )

    # initialize ClickUp client ---------------------------------------------------------------
    clickup_client = pyclickup.ClickUp(clickup_token)

    # list teams and exit
    if do_list_clickup_teams:
        list_clickup_teams(clickup_client)
        return 0

    # list lists and exit
    if do_list_clickup_lists:
        if not clickup_team_id:
            error_and_exit(
                "You must provide a ClickUp team ID using --clickup-team-id to list lists",
            )
        list_clickup_lists(clickup_client, clickup_team_id)
        return 0

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            side_A_name="Taskwarrior",
            side_B_name="ClickUp",
            combination=combination_name,
        )
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        tw_sync_all_tasks = app_config["tw_sync_all_tasks"]
        clickup_list_id = app_config["clickup_list_id"]
        clickup_team_id = app_config["clickup_team_id"]
    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "clickup_list_id": clickup_list_id,
                "clickup_team_id": clickup_team_id,
                "tw_project": tw_project,
                "tw_tags": tw_tags,
            },
            config_fname="tw_clickup_configs",
            custom_combination_savename=custom_combination_savename,
        )

    # validate required fields ----------------------------------------------------------------
    if not clickup_list_id:
        error_and_exit("You must provide a ClickUp list ID using --clickup-list-id")
    if not clickup_team_id:
        error_and_exit("You must provide a ClickUp team ID using --clickup-team-id")

    # more checks -----------------------------------------------------------------------------
    combination_of_tw_related_options = any([tw_filter_li, tw_tags, tw_project])
    check_required_mutually_exclusive(
        tw_sync_all_tasks,
        combination_of_tw_related_options,
        "sync_all_tw_tasks",
        "combination of specific TW-related options",
    )

    # announce configuration ------------------------------------------------------------------
    logger.info(
        format_dict(
            header="Configuration",
            items={
                "TW Filter": " ".join(tw_filter_li),
                "TW Tags": tw_tags,
                "TW Project": tw_project,
                "TW Sync All Tasks": tw_sync_all_tasks,
                "ClickUp List ID": clickup_list_id,
                "ClickUp Team ID": clickup_team_id,
            },
            prefix="\n\n",
            suffix="\n",
        ),
    )
    if confirm:
        confirm_before_proceeding()

    # initialize sides ------------------------------------------------------------------------
    tw_side = TaskWarriorSide(
        tw_filter=" ".join(tw_filter_li),
        tags=tw_tags,
        project=tw_project,
    )

    clickup_side = ClickUpSide(
        client=clickup_client,
        list_id=clickup_list_id,
        team_id=clickup_team_id,
    )

    # teardown function and exception handling ------------------------------------------------
    register_teardown_handler(
        pdb_on_error=pdb_on_error,
        inform_about_config=inform_about_config,
        combination_name=combination_name,
        verbose=verbose,
    )

    # sync ------------------------------------------------------------------------------------
    with Aggregator(
        side_A=clickup_side,
        side_B=tw_side,
        converter_A_to_B=convert_clickup_to_tw,
        converter_B_to_A=convert_tw_to_clickup,
        resolution_strategy=get_resolution_strategy(
            resolution_strategy,
            side_A_type=type(clickup_side),
            side_B_type=type(tw_side),
        ),
        config_fname=combination_name,
        ignore_keys=(
            (
                "date_created",
                "date_updated",
                "date_closed",
            ),
            ("end", "entry", "modified", "urgency"),
        ),
    ) as aggregator:
        aggregator.sync()

    return 0


if __name__ == "__main__":
    sys.exit(main())
