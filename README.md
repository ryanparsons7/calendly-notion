# event_importer

Imports Events from Calendly and creates them in Notion DB

## Requirements:

The following example environmental variables need to exist:
```sh
#The ID of the Notion database you want events to be generated in.
NOTION_DB_ID=nearx9y2ejcyrgxe224i4xmvic7fyzh4
#The bearer token of the Notion integration to use. Have this kept secret.
NOTION_BEARER_TOKEN=yp9b54bc24u74apry4ce8qzmqiieeyjba33tpvffdbznh4i0ex
#The bearer token of the Calendly integration to use. Have this kept secret.
CALENDLY_TOKEN=XXXXXXX
#The org uri in calendly. Have this kept secret.
CALENDLY_ORG=https://api.calendly.com/organizations/7a8b9c12-345d-678e-f012-3g456h789ijk
#The prefix to add at the beginning of each ticket ID
LINK_PREFIX=https://example.com/ticket/
```