from logger import get_logger
from notion_api import NotionAPI

logger = get_logger(__name__)

class SchemaManager:
    def __init__(self, notion_api: NotionAPI):
        self.notion_api = notion_api

    def ensure_schema(self, data_source_id: str, required_schema: dict) -> list:
        """
        Ensures that the data source has the required schema.
        Handles property creation and title property renaming.
        Returns the list of available property names after update.
        """
        try:
            current_properties = self.notion_api.get_data_source_properties(data_source_id)
            logger.info(f"Current properties: {list(current_properties.keys())}")
            
            properties_to_update = {}

            # Check for title property renaming
            # Notion only allows one title property. If we have one with a different name, we must rename it.
            existing_title_prop_name = None
            for prop_name, prop_data in current_properties.items():
                if prop_data.get("type") == "title":
                    existing_title_prop_name = prop_name
                    break
            
            if existing_title_prop_name and existing_title_prop_name != "Title":
                logger.info(f"Renaming title property from '{existing_title_prop_name}' to 'Title'")
                properties_to_update[existing_title_prop_name] = {"name": "Title"}
                # Update current_properties locally so we don't try to create 'Title' as a new property below
                current_properties["Title"] = current_properties.pop(existing_title_prop_name)
            
            for name, config in required_schema.items():
                if name not in current_properties:
                    properties_to_update[name] = config
            
            if properties_to_update:
                logger.info(f"Updating data source schema. Changes: {list(properties_to_update.keys())}")
                self.notion_api.update_data_source_properties(data_source_id, properties_to_update)
                logger.info("Data source schema updated successfully.")
                
                # Construct the final list of properties
                final_properties = list(current_properties.keys())
                for name in properties_to_update:
                    # If it was a rename, the new name "Title" is already in current_properties (we added it above)
                    # If it was a new property, we need to add it
                    if name not in final_properties and "name" not in properties_to_update[name]:
                         final_properties.append(name)
                
                return final_properties
            else:
                logger.info("Data source schema is up to date.")
                return list(current_properties.keys())
                
        except Exception as e:
            logger.warning(f"Failed to ensure schema: {e}")
            return []
