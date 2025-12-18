"""ClickUp utilities."""

from bubop import logger


def list_clickup_lists(client, team_id: str):
    """List all available ClickUp lists in the workspace.
    
    Args:
        client: The pyclickup client instance
        team_id: The team/workspace ID
    """
    logger.info("Fetching ClickUp lists...")
    
    try:
        team = client.get_team_by_id(team_id)
        
        for space in team.spaces:
            logger.info(f"\nSpace: {space.name} (ID: {space.id})")
            
            for project in space.projects:
                logger.info(f"  Project: {project.name} (ID: {project.id})")
                
                for list_item in project.lists:
                    logger.info(f"    List: {list_item.name} (ID: {list_item.id})")
                    
    except Exception as e:
        logger.error(f"Error listing ClickUp lists: {e}")


def list_clickup_teams(client):
    """List all available ClickUp teams/workspaces.
    
    Args:
        client: The pyclickup client instance
    """
    logger.info("Fetching ClickUp teams/workspaces...")
    
    try:
        teams = client.teams
        
        for team in teams:
            logger.info(f"Team: {team.name} (ID: {team.id})")
            
    except Exception as e:
        logger.error(f"Error listing ClickUp teams: {e}")
