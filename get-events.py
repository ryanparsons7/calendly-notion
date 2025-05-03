import datetime
import os
import re
import requests
from dotenv import load_dotenv
import time


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

def getCalendlyEvents(startTime, endTime, syncCallTime, orgId, linkPrefix, token):
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
                "external_id": event.get('calendar_event', {}).get('external_id'),
                "start_time": event.get('start_time'),
                "email": event.get('event_memberships', [{}])[0].get('user_email'),
                "ticketNumber": getEventInviteeTicketNumber(eventUri, token)
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

def main():
    # Load the environmental variables and drop them into variables to use later.
    load_dotenv()
    token = os.getenv("NOTION_BEARER_TOKEN")
    notionDB = os.getenv("NOTION_DB_ID")
    syncCallTime = os.getenv("SYNC_CALL_TIME")
    calendlyToken = os.getenv("CALENDLY_TOKEN")
    calendlyOrg = os.getenv("CALENDLY_ORG")
    LinkPrefix = os.getenv("LINK_PREFIX")

    today = datetime.date.today() # Set variable for today.
    week = today + datetime.timedelta(days=7) # set variable for a week from now.

    # Set the start time for the search to today at 0:00:00 UTC.
    startTime = (
            datetime.datetime.now(datetime.UTC)
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
    # Set the end time for the search for 7 days from now at the very end of the day UTC.
    endTime = (
        datetime.datetime.now(datetime.UTC)
        .replace(
            tzinfo=None,
            year=week.year,
            month=week.month,
            day=week.day,
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )
        .isoformat()
        + "Z"
        )
    
    events = getCalendlyEvents(startTime, endTime, syncCallTime, calendlyOrg, LinkPrefix, calendlyToken)
    if not events:
        print("The events array is empty, exiting the program.")
        return
    else:
        # Call another function here, for example:
        print("Events fetched successfully.")

if __name__ == "__main__":
    print("Version 1")
    main()
