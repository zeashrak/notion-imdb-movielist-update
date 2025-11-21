
REQUIRED_PROPERTIES = {
    "Title": {"title": {}},
    "IMDB": {"url": {}},
    "Director/Creator": {"select": {}},
    "Duration [min]": {"number": {"format": "number"}},
    "IMDB Rating": {"number": {"format": "number"}},
    "Description": {"rich_text": {}},
    "Genre": {"multi_select": {}},
    "Sync Status": {
        "select": {
            "options": [
                {"name": "Updated", "color": "green"},
                {"name": "Not Found", "color": "red"},
                {"name": "Pending", "color": "gray"}
            ]
        }
    }
}
