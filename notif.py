from curl_cffi import requests
from datetime import datetime, date
from searchurl import SearchURL
from projectenums import BusCategory
from zoneinfo import ZoneInfo

def get_inventory(category: BusCategory) -> dict:
    ist_now = datetime.now(ZoneInfo("Asia/Kolkata"))

    doj = ist_now.today()
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

    response = requests.post(
        url.get_formatted_url(), 
        headers=headers, 
        json=payload,
        impersonate="chrome"
    )

    res_json: dict = response.json()

    if 'success' not in res_json.keys() or not res_json['success']:
        return {}

    data = res_json["data"]
    inventories = data["inventories"]

    return inventories

def send_notification(title: str, message:str):
    requests.post(
        url=f"https://ntfy.sh/jam_rjt_bus_status_chavda_parth",
        data=message.encode('utf-8'),
        headers={
            "Title": title,
            "Priority": "high",
            "Tags": "bus"
        }
    )

private_inventory = get_inventory(category=BusCategory.PRIVATE)
gt_seats = 0

for bus in private_inventory:
    name = bus["travelsName"]
    dep_time = bus["departureTime"].split(" ")[1][:5]
    current_time = datetime.now().strftime("%H:%M")

    if "Gujarat Travels Agency" and (current_time < "07:00" and dep_time <= "07:00"):
        gt_seats = bus["availableSeats"]
        break


if (gt_seats > 5):
    send_notification(
        title="Gujarat Travels Seats Available!",
        message=f"Available Seats: {gt_seats}"
    )
else:
    gsrtc_inventory = get_inventory(BusCategory.GSRTC)
    bus_count = 0
    
    for bus in gsrtc_inventory:
        dep_time = bus["departureTime"].split(" ")[1][:5]
        current_time = datetime.now().strftime("%H:%M")

        if current_time < dep_time and dep_time <= "07:30":
            bus_count += 1

    if (bus_count > 0):
        send_notification(
            title="Gujarat Travels Not Available",
            message=f"GSRTC Buses: {bus_count} Available"
        )
    else:
        send_notification(
            title="Could not find buses.",
            message="No updates available."
        )
