from curl_cffi import requests
from datetime import datetime, date, timezone, timedelta
from searchurl import SearchURL
from projectenums import BusCategory
from zoneinfo import ZoneInfo
import os
import logging

year = os.environ.get("YEAR")
month = os.environ.get("MONTH")
day =  os.environ.get("DATE"),
hour = os.environ.get("HOUR"),
minute = os.environ.get("MINUTE"),
second = os.environ.get("SECOND"),

ist_now = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), 1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# logger.info(f"UTC Time: {utc_date}")
logger.info(f"IST Time: {ist_now}")

def get_inventory(category: BusCategory) -> dict:
    doj=ist_now.date()
    travelsList = []
    url = SearchURL(doj, 50, category)

    if url.groupId != 0:
        travelsList.append(url.groupId)

    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "origin": "https://www.redbus.in",
        "referer": "https://www.redbus.in/bus-tickets/jamnagar-to-rajkot"
    }

    payload = {
        "appliedFilterCount": 0,
        "onlyShow": [],
        "dt": [],
        "SeaterType": [],
        "AcType": [],
        "travelsList": travelsList,
        "amtLst": [],
        "bpList": [],
        "dpList": [],
        "CampaignFilter": [],
        "at": [],
        "persuasionList": [],
        "priceRange": [],
        "RouteIds": [],
        "bpKeys": [],
        "dpKeys": [],
        "streaksFilter": [],
        "preRouteFilters": None
    }

    request_url = url.get_formatted_url()
    logger.info("Fetching inventory for %s from %s", category.name, request_url)

    response = requests.post(
        url=request_url,
        headers=headers,
        json=payload,
        impersonate="chrome"
    )
    logger.info("Inventory request for %s completed with status %s", category.name, response.status_code)

    try:
        res_json: dict = response.json()
    except ValueError as exc:
        logger.exception("Failed to decode JSON response for %s: %s", category.name, exc)
        return {}

    if 'success' not in res_json.keys() or not res_json['success']:
        logger.warning("Inventory request for %s was unsuccessful: %s", category.name, res_json)
        return {}

    data = res_json["data"]
    inventories = data["inventories"]
    logger.info("Received %d inventory entries for %s", len(inventories), category.name)

    return inventories


def send_notification(title: str, message: str):
    logger.info("Sending notification: %s - %s", title, message)
    response = requests.post(
        url=f"https://ntfy.sh/jam_rjt_bus_status_chavda_parth",
        data=message.encode('utf-8'),
        headers={
            "Title": title,
            "Priority": "high",
            "Tags": "bus"
        }
    )
    logger.info("Notification dispatched with status %s", response.status_code)


private_inventory = get_inventory(category=BusCategory.PRIVATE)
logger.info("Private inventory result count: %s", len(private_inventory))

gt_seats = 0
current_time = ist_now.strftime("%H:%M")
gt_dep_time = "Not found"

for bus in private_inventory:
    name = bus["travelsName"]
    dep_time = bus["departureTime"].split(" ")[1][:5]
    logger.info("Checking private bus %s at %s; current time %s", name, dep_time, current_time)

    if "Gujarat Travels Agency" and (current_time < "07:00" and dep_time <= "07:00"):
        gt_seats = bus["availableSeats"]
        gt_dep_time = dep_time
        logger.info("Selected Gujarat Travels availability: %s seats at %s", gt_seats, dep_time)
        break


if (gt_seats > 5):
    logger.info("Sending Gujarat Travels seats available notification with %s seats", gt_seats)
    send_notification(
        title=f"{gt_seats} available in Gujarat Travels",
        message=f"Departure Time: {gt_dep_time}"
    )
else:
    gsrtc_inventory = get_inventory(BusCategory.GSRTC)
    bus_count = 0
    bus_times = []
    logger.info("Checking GSRTC inventory count: %s", len(gsrtc_inventory))

    for bus in gsrtc_inventory:
        dep_time = bus["departureTime"].split(" ")[1][:5]
        logger.info("Evaluating GSRTC bus departure %s at current time %s", dep_time, current_time)

        if current_time < dep_time and dep_time <= "07:30":
            bus_count += 1
            bus_times.append(dep_time)
            logger.info("GSRTC bus available before 07:30: %s", dep_time)

    if (bus_count > 0):
        logger.info("Sending GSRTC buses available notification: %s buses", bus_count)
        send_notification(
            title="Gujarat Travels Not Available",
            message=f"{bus_count} GSRTC Buses Available. Timings: {bus_times}"
        )
    else:
        logger.warning("No suitable buses found for the current time window")
        send_notification(
            title="Could not find buses.",
            message="No updates available."
        )
