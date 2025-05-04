# event_importer

Imports Events from Calendly and creates them in Notion DB

## Requirements:

The following example environmental variables need to exist:
```sh
# The ID of the Notion database you want events to be generated in.
NOTION_DB_ID=XXXXXXX
# The bearer token of the Notion integration to use.
NOTION_BEARER_TOKEN=XXXXXXX
# The bearer token of the Calendly integration to use.
CALENDLY_TOKEN=XXXXXXX
# The org uri in calendly.
CALENDLY_ORG=https://api.calendly.com/organizations/XXXXXXX
# The prefix to add at the beginning of each ticket ID
LINK_PREFIX=https://example.com/ticket/
# The number of days to look ahead for events during the search.
EVENT_SEARCH_DAYS=7
```