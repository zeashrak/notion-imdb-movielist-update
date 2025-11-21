import re
from notion_client import Client
from exceptions import NotionAPIError
from logger import get_logger

logger = get_logger(__name__)

class NotionAPI:
    def __init__(self, notion_token: str):
        self.client = Client(auth=notion_token)

    def get_data_source_properties(self, data_source_id: str) -> dict:
        try:
            ds = self.client.data_sources.retrieve(data_source_id)
            return ds.get("properties", {})
        except Exception as e:
            logger.warning(f"Failed to retrieve data source properties: {e}")
            raise NotionAPIError(f"Failed to retrieve data source properties: {e}")

    def update_data_source_properties(self, data_source_id: str, properties: dict):
        try:
            self.client.data_sources.update(data_source_id=data_source_id, properties=properties)
        except Exception as e:
            logger.warning(f"Failed to update data source properties: {e}")
            raise NotionAPIError(f"Failed to update data source properties: {e}")


    def find_database_id(self, database_name: str) -> str:
        try:
            results = self.client.search(query=database_name, filter={
                "property": "object",
                "value": "data_source"
            }).get("results")
            
            if not results:
                raise NotionAPIError(f"Database (Data Source) '{database_name}' not found.")
            return results[0]["id"]
        except Exception as e:
            raise NotionAPIError(f"Error finding database: {e}")

    def get_data_source_id_from_database_id(self, database_id: str) -> str:
        try:
            db = self.client.databases.retrieve(database_id)
            if "data_sources" in db and db["data_sources"]:
                return db["data_sources"][0]["id"]
            
            try:
                ds = self.client.data_sources.retrieve(database_id)
                return ds["id"]
            except:
                pass

            raise NotionAPIError(f"Could not find data source for ID: {database_id}")
        except Exception as e:
             try:
                 ds = self.client.data_sources.retrieve(database_id)
                 return ds["id"]
             except:
                 raise NotionAPIError(f"Error resolving data source ID from {database_id}: {e}")

    def find_data_source_id_by_url_id(self, url_id: str) -> str:
        return self.get_data_source_id_from_database_id(url_id)

    def get_empty_pages(self, database_id: str, available_properties: list = None) -> list:
        and_filters = [
            {
                "or": [
                    {
                        "property": "Title",
                        "title": {
                            "is_not_empty": True
                        }
                    },
                    {
                        "property": "IMDB",
                        "url": {
                            "is_not_empty": True
                        }
                    }
                ]
            },
            {
                "or": [
                    {
                        "property": "Duration [min]",
                        "number": {
                            "is_empty": True
                        }
                    },
                    {
                        "property": "Director/Creator",
                        "select": {
                            "is_empty": True
                        }
                    },
                    {
                        "property": "IMDB",
                        "url": {
                            "is_empty": True
                        }
                    }
                ]
            }
        ]

        if available_properties and "Sync Status" in available_properties:
            and_filters.insert(0, {
                "property": "Sync Status",
                "select": {
                    "is_empty": True
                }
            })

        empty_page_filter = {
            "filter": {
                "and": and_filters
            }
        }
        try:
            return self.client.data_sources.query(data_source_id=database_id, **empty_page_filter).get("results")
        except Exception as e:
            raise NotionAPIError(f"Error getting empty pages: {e}")

    def update_page(self, page_id: str, properties: dict):
        try:
            self.client.pages.update(page_id=page_id, properties=properties)
        except Exception as e:
            raise NotionAPIError(f"Error updating page: {e}")

    def retrieve_page(self, page_id: str) -> dict:
        try:
            return self.client.pages.retrieve(page_id=page_id)
        except Exception as e:
            raise NotionAPIError(f"Error retrieving page: {e}")

    @staticmethod
    def get_database_id_from_url(database_url: str) -> str | None:
        result = re.search(r"notion\.so/[^/]+/(\w+)", database_url)
        if result:
            result = result.group(1)
            if len(result) == 32:
                return f"{result[:8]}-{result[8:12]}-{result[12:16]}-{result[16:20]}-{result[20:]}"
        return None
