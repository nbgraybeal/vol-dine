
import requests
from bs4 import BeautifulSoup
import json
import html

URL = "https://dining.utk.edu/vendor/stokely-dining-hall/"

print("Downloading Stokely Dining Hall menu...")

response = requests.get(URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

menu_data = None

# Search all HTML elements and their attributes
for element in soup.find_all(True):
    for attribute, value in element.attrs.items():

        if isinstance(value, list):
            value = " ".join(value)

        if not isinstance(value, str):
            continue

        if "subLocations" not in value:
            continue

        try:
            decoded = html.unescape(value)
            parsed = json.loads(decoded)

            if isinstance(parsed, dict) and "subLocations" in parsed:
                menu_data = parsed
                print("SUCCESS: Extracted menu JSON!")
                break

        except json.JSONDecodeError:
            continue

    if menu_data is not None:
        break

if menu_data is None:
    print("Could not extract menu JSON.")
    print("The data may be embedded inside a JavaScript variable.")
    raise SystemExit(1)

from datetime import datetime, timezone
from pathlib import Path

output = {
    "location": "Stokely Dining Hall",
    "retrieved_at": datetime.now(timezone.utc).isoformat(),
    "stations": menu_data["subLocations"]
}

Path("data").mkdir(exist_ok=True)

with open("data/stokely.json", "w", encoding="utf-8") as file:
    json.dump(output, file, indent=2, ensure_ascii=False)

print("SUCCESS: Saved menu to data/stokely.json")

print("\nSTOKELY DINING HALL")

for station in menu_data["subLocations"].values():

    station_name = station.get("name", "Unknown station")

    for meal in station.get("mealPeriods", {}).values():

        meal_name = meal.get("name", "Unknown meal")

        print(f"\n{station_name.upper()} - {meal_name.upper()}")
        print("-" * 40)

        for item in meal.get("menuItems", []):

            name = item.get("name", "Unknown item")
            nutrition = item.get("nutrition") or {}
            attributes = nutrition.get("primary_attributes") or {}
            calories = attributes.get("calories", {}).get("value", "?")

            print(f"  {name} ({calories} calories)")
