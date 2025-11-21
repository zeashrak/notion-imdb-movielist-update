import sys
from typing import List, Dict, Any, Tuple

import config
from imdbinfo_adapter import IMDbInfoAdapter
from logger import get_logger
from notion_api import NotionAPI
from exceptions import NotionAPIError
from updater import Updater
from notion_page import NotionPage
from schema import REQUIRED_PROPERTIES
from schema_manager import SchemaManager

logger = get_logger(__name__)

def _get_database_ids(notion_api: NotionAPI) -> Tuple[str | None, str | None]:
    """
    Gets the database IDs.
    Returns (database_id_for_schema_update, data_source_id_for_query).
    """
    if config.NOTION_DATABASE_URL:
        url_id = notion_api.get_database_id_from_url(config.NOTION_DATABASE_URL)
        if url_id:
            try:
                # Resolve to Data Source ID using the Discovery Step
                ds_id = notion_api.get_data_source_id_from_database_id(url_id)
                return url_id, ds_id
            except NotionAPIError as e:
                logger.warning(f"Failed to resolve data source ID from URL ID: {e}")
                # Fallback to using the ID directly
                return url_id, url_id
    
    if config.NOTION_DATABASE_NAME:
        ds_id = notion_api.find_database_id(config.NOTION_DATABASE_NAME)
        # We can't easily determine the database ID for schema update from just the name search for data_source
        return None, ds_id
    
    return None, None

def _process_pages(pages: List[Dict[str, Any]], updater: Updater, available_properties: List[str] = None):
    """Processes a list of Notion pages."""
    if not pages:
        logger.info("No entries found to update.")
        return

    logger.info(f"Found {len(pages)} empty entries. Updating now...")
    for page_data in pages:
        title = None
        if page_data["properties"]["Title"]["title"]:
            title = page_data["properties"]["Title"]["title"][0]["text"]["content"]

        page = NotionPage(
            id=page_data["id"],
            title=title,
            imdb_url=page_data["properties"]["IMDB"]["url"]
        )
        updater.update_page(page, available_properties)

def main():
    if not config.NOTION_TOKEN:
        logger.error("NOTION_TOKEN not found.")
        sys.exit(1)

    try:
        notion_api = NotionAPI(config.NOTION_TOKEN)
        imdb_adapter = IMDbInfoAdapter()
        updater = Updater(notion_api, imdb_adapter)

        schema_db_id, query_ds_id = _get_database_ids(notion_api)
        if not query_ds_id:
            logger.error("Database could not be found. Please check your configuration.")
            sys.exit(1)

        available_properties = []
        if query_ds_id:
            schema_manager = SchemaManager(notion_api)
            available_properties = schema_manager.ensure_schema(query_ds_id, REQUIRED_PROPERTIES)

        if "Sync Status" not in available_properties:
            logger.warning("Property 'Sync Status' is missing. Automatic skipping of checked items will be disabled. Please add 'Sync Status' (Select) property to your Notion database manually.")

        pages = notion_api.get_empty_pages(database_id=query_ds_id, available_properties=available_properties)
        _process_pages(pages, updater, available_properties)

        logger.info("Finished")

    except NotionAPIError as e:
        logger.error(f"A critical Notion API error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
