# Sequence Diagram

This diagram details the step-by-step logic of the main update process. It shows how the different objects in your code interact with each other in order to find and update a movie page in Notion.

```mermaid
sequenceDiagram
    participant Main as main.py
    participant SchemaManager
    participant Updater
    participant NotionAPI
    participant IMDbAdapter

    Main->>NotionAPI: get_data_source_id_from_database_id(db_id)
    NotionAPI-->>Main: Returns data_source_id
    
    Main->>SchemaManager: ensure_schema(data_source_id, REQUIRED_PROPERTIES)
    SchemaManager->>NotionAPI: get_data_source_properties(data_source_id)
    NotionAPI-->>SchemaManager: Returns current properties
    opt Schema needs update
        SchemaManager->>NotionAPI: update_data_source_properties(data_source_id, new_props)
        NotionAPI-->>SchemaManager: Confirms update
    end
    SchemaManager-->>Main: Returns available_properties

    Main->>NotionAPI: get_empty_pages(data_source_id, available_properties)
    NotionAPI-->>Main: Returns list of pages
    loop For each page
        Main->>Updater: update_page(page, available_properties)
        Updater->>IMDbAdapter: search_movie(title) or get_movie(id)
        IMDbAdapter-->>Updater: Returns Movie object
        Updater->>NotionAPI: update_page(page_id, properties)
        NotionAPI-->>Updater: Confirms update
    end
```
