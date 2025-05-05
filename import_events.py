import datetime
import os
import requests
from dotenv import load_dotenv
from dateutil import tz

def getEventInviteeTicketNumber(event_id, token):
    """
    Fetches the answer to the "Ticket Number" question for a specific event invitee.

    Args:
        event_id (str): The ID of the Calendly event.
        token (str): The Calendly API token for authentication.

    Returns:
        str: The answer to the "Ticket Number" question, or None if not found.
    """
    # Define the Calendly API endpoint for fetching event invitees.
    url = f"https://api.calendly.com/scheduled_events/{event_id}/invitees"

    # Set up the headers for the API request, including the authorization token.
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        # Make a GET request to the Calendly API with the specified headers.
        response = requests.get(url, headers=headers)
        
        # Raise an exception if the request was unsuccessful.
        response.raise_for_status()
        
        # Parse the JSON response and extract the list of invitees.
        invitees = response.json().get("collection", [])
        
        # Iterate through the invitees to find the answer to the "Ticket Number" question.
        for invitee in invitees:
            questions_and_answers = invitee.get("questions_and_answers", [])
            for qa in questions_and_answers:
                if qa.get("question") == "Ticket Number":
                    return qa.get("answer")
        
        # Return None if the "Ticket Number" question is not found.
        return None
    except requests.exceptions.RequestException as e:
        # Print an error message if the API request fails and return None.
        print(f"Error fetching invitee ticket number: {e}")
        return None

def getCalendlyEvents(startTime, endTime, orgId, linkPrefix, token):
    """
    Fetches scheduled events from the Calendly API within a specified time range.

    Args:
        startTime (str): The start time for the event search in ISO 8601 format.
        endTime (str): The end time for the event search in ISO 8601 format.
        syncCallTime (str): The synchronization call time (not used in this function).
        orgId (str): The Calendly organization ID.
        linkPrefix (str): The link prefix for the events (not used in this function).
        token (str): The Calendly API token for authentication.

    Returns:
        list: A list of events retrieved from the Calendly API.
    """
    # Define the Calendly API endpoint for fetching scheduled events.
    url = f"https://api.calendly.com/scheduled_events"
    
    # Set up the headers for the API request, including the authorization token.
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    # Define the query parameters for the API request, including the organization ID,
    # event status, count, and the time range for the search.
    params = {
        "organization": orgId,
        "status": "active",
        "count": 100,
        "min_start_time": startTime,
        "max_start_time": endTime
    }

    eventsInfo = []  # Initialize an empty list to store event information.

    try:
        # Make a GET request to the Calendly API with the specified headers and parameters.
        response = requests.get(url, headers=headers, params=params)
        
        # Raise an exception if the request was unsuccessful.
        response.raise_for_status()
        
        # Parse the JSON response and extract the list of events.
        events = response.json().get("collection", [])
        
        # Iterate through the events and print their details.
        for event in events:
            eventUri = event.get('uri').split('/')[-1]
            event_details = {
                "id": event.get('calendar_event', {}).get('external_id'),
                "startTime": event.get('start_time'),
                "email": event.get('event_memberships', [{}])[0].get('user_email'),
                "ticketLink": (f'{linkPrefix}{getEventInviteeTicketNumber(eventUri, token)}')
            }
            eventsInfo.append(event_details)
        # Count the number of events captured and print the count.
        print(f"Number of events captured: {len(eventsInfo)}")
        # Return the list of events.
        return eventsInfo
    except requests.exceptions.RequestException as e:
        # Print an error message if the API request fails and return an empty list.
        print(f"Error fetching events: {e}")
        return []


def createNotionDatabasePages(bearerToken, databaseID, eventsArray, userDict):
    """
    Takes in array of dicts of call events, and database ID and also a dict of users (email-ID)
    Creates pages in the database with these events.
    """

    # URL for the notion page endpoint
    url = "https://api.notion.com/v1/pages"

    # Define headers needed, including the bearer token for authentication.
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearerToken}",
        "Notion-Version": "2022-06-28",
    }

    # Iterate through the events array.
    for event in eventsArray:
        email = event.get("email")  # String
        ticketLink = event.get("ticketLink")  # String
        startTime = event.get("startTime")  # String in format 2024-11-29T20:15:00Z
        startTime = (
            startTime[:-1] + "+00:00"
        )  # Converts from Zulu time format to supported format.
        eventID = event.get("id")  # Bool
        emptyPerson = False

        # See if the user email exists in the user list we got earlier.
        try:
            userID = userDict[email] # If it exists, set the user ID.
        except:
            print("User not found in the Workspace with the same email. Setting Person field as empty for this event.")
            emptyPerson = True # If it errors out, just set this variable to true, so we exclude adding a person to the event.

        myjson = {
            "parent": {
                "type": "database_id",
                "database_id": databaseID,
            },
            "properties": {
                "Event ID": {
                    "title": [{"type": "text", "text": {"content": eventID}}]
                },
                "Summary": {
                    "rich_text": [{"type": "text", "text": {"content": "Please Update"}}]
                },
                "Person(s)": {
                    "people": [{"id": userID}]
                },
                "Ticket URL": {"url": ticketLink},
                "Date & Time (Local)": {
                    "date": {
                        "start": startTime,
                        "end": None,
                        "time_zone": None,
                    }
                },
                "Shadow Friendly?": {"type": "select", "select": {"name": "Unknown"}},
                "Status": {"type": "select", "select": {"name": "Upcoming Call"}},
            },
        }

        if emptyPerson: # If the person ID was not found in the user list
            for key in myjson: # Iterate through the keys
                myjson[key].pop('Person(s)', None) # And remove the Person field key to prevent issues when adding to the DB


        if not (isEventPresentInDB(bearerToken, databaseID, eventID)):
            print(f"Attempting to create event in DB with ID {eventID}.")
            try:
                # Make a GET request to the Calendly API with the specified headers and parameters.
                x = requests.post(url, headers=headers, json=myjson)
                
                # Raise an exception if the request was unsuccessful.
                x.raise_for_status()
                print(x)
            except requests.exceptions.RequestException as e:
                # Print an error message if the API request fails and return an empty list.
                print(f"Error create event in Notion DB: {e}")
                return
        else:
            print(f"Event with ID {eventID} already exists, checking if start time needs updating.")
            doesEventNeedUpdating(bearerToken, databaseID, eventID, startTime)
        # print the response text (the content of the requested file):
        # print(x.text)

def doesEventNeedUpdating(bearerToken, notionDB, eventID, startTime):
    url = f"https://api.notion.com/v1/databases/{notionDB}/query"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearerToken}",
        "Notion-Version": "2022-06-28",
    }

    myjson = {
        "filter": {
            "and": [
                {
                    "property": "Event ID",
                    "title": {"equals": eventID},
                }
            ]
        }
    }

    x = requests.post(url, headers=headers, json=myjson)
    x.raise_for_status()
    jsonOutput = x.json()
    currentTime = jsonOutput["results"][0]["properties"]["Date & Time (Local)"]["date"]["start"]
    pageID = jsonOutput["results"][0]["id"]
    startTime = datetime.datetime.fromisoformat(startTime)
    currentTime = datetime.datetime.fromisoformat(currentTime)
    if (startTime == currentTime):
        print("Times match, no action needed.")
    else:
        print("Times do not match, update to start time needed.")
        updateStartTime(bearerToken, pageID, startTime)


def updateStartTime(bearerToken, pageID, newStartTime):
    url = f"https://api.notion.com/v1/pages/{pageID}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearerToken}",
        "Notion-Version": "2022-06-28",
    }

    newStartTime = str(newStartTime)

    myjson = {
        "properties": {
            "Date & Time (Local)": {
            "date": {
                "start": newStartTime,
                },
            },
        },
    }
    print(f"Updating start time to {newStartTime} for page ID {pageID}.")
    x = requests.patch(url, headers=headers, json=myjson)
    print(x)


def isEventPresentInDB(bearerToken, notionDB, eventID):
    url = f"https://api.notion.com/v1/databases/{notionDB}/query"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearerToken}",
        "Notion-Version": "2022-06-28",
    }

    myjson = {
        "filter": {
            "and": [
                {
                    "property": "Event ID",
                    "title": {"equals": eventID},
                }
            ]
        }
    }
    x = requests.post(url, headers=headers, json=myjson)
    jsonOutput = x.json()
    exists = bool(jsonOutput["results"])
    return(exists)

def getUsers(bearerToken):
    """
    The point of this is to be run once at the start of the script to get a dict generated, with each entry being a email address with the value being their notion user ID.
    """
    # URL for the request to check users in Notion.
    url = "https://api.notion.com/v1/users"
    # Required headers, include the bearer token for authentication.
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearerToken}",
        "Notion-Version": "2022-06-28",
    }
    # Setting empty dictionary for the user emails and IDs.
    userDict = {}

    print("Getting current users in Workspace.")
    x = requests.get(url, headers=headers)
    print(x)

    jsonOutput = x.json()
    jsonOutput = jsonOutput["results"]

    for user in jsonOutput:
        try:
            email = user["person"]["email"]
        except:
            continue # If a email doesn't exist for a user entry, skip adding them to the dict.
        id = user["id"] # Literally every user has an ID, shouldn't fail. ;)
        userDict[email] = id # Add them to the dict.
    
    return userDict


def main():
    # Load the environmental variables and drop them into variables to use later.
    load_dotenv()
    notionToken = os.getenv("NOTION_BEARER_TOKEN")
    calendlyToken = os.getenv("CALENDLY_TOKEN")
    notionDB = os.getenv("NOTION_DB_ID")
    LinkPrefix = os.getenv("LINK_PREFIX")
    orgId = os.getenv("CALENDLY_ORG")
    daysCount = os.getenv("EVENT_SEARCH_DAYS")

    today = datetime.date.today() # Set variable for today.
    endSearch = today + datetime.timedelta(days=int(daysCount)) # set variable for end of search.
    print(f"Search range for events from {today} to {endSearch}.")

    # Set the start time for the search to today at 0:00:00 UTC.
    startTime = (
            datetime.datetime.now(tz.UTC)
            .replace(
                tzinfo=None,
                year=today.year,
                month=today.month,
                day=today.day,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            .isoformat()
            + "Z"
        )
    # Set the end time for the search for the number days from now at the very end of the day UTC.
    endTime = (
        datetime.datetime.now(tz.UTC)
        .replace(
            tzinfo=None,
            year=endSearch.year,
            month=endSearch.month,
            day=endSearch.day,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )
        .isoformat()
        + "Z"
        )
    
    userList = getUsers(notionToken) # Get the user dictionary list.
    eventData = getCalendlyEvents(startTime, endTime, orgId, LinkPrefix, calendlyToken) # Grab the event data from Google Calendar.
    createNotionDatabasePages(notionToken, notionDB, eventData, userList) # Create the notion database pages with the event data.

if __name__ == "__main__":
    print("Version 1")
    main()
