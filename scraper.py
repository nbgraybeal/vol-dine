
import requests
from bs4 import BeautifulSoup
import json
import html
from pathlib import Path
from datetime import datetime, timezone

DINING_HALLS = {
    "stokely": {
        "name": "Stokely Dining Hall",
        "url": "https://dining.utk.edu/vendor/stokely-dining-hall/"
    },
    "rocky-top": {
        "name": "Rocky Top Dining Hall",
        "url": "https://dining.utk.edu/vendor/rocky-top-dining-hall/"
    },
    "southern-kitchen": {
        "name": "Southern Kitchen",
        "url": "https://dining.utk.edu/vendor/southern-kitchen/"
    }
}

DATA_FOLDER = Path(__file__).resolve().parent / "data"
DATA_FOLDER.mkdir(exist_ok=True)


def extract_menu(page_html):
    soup = BeautifulSoup(page_html, "html.parser")

    for element in soup.find_all(True):
        for value in element.attrs.values():
            if isinstance(value, list):
                value = " ".join(value)

            if not isinstance(value, str):
                continue

            if "subLocations" not in value:
                continue

            try:
                data = json.loads(html.unescape(value))
                if isinstance(data, dict) and isinstance(
                    data.get("subLocations"), dict
                ):
                    return data
            except (ValueError, TypeError):
                continue

    return None


def update_hall(key, hall):
    print(f"\nDownloading {hall['name']}...")

    response = requests.get(
        hall["url"],
        timeout=30,
        headers={"User-Agent": "VolDine/1.0 (menu viewer)"}
    )
    response.raise_for_status()

    menu = extract_menu(response.text)

    if menu is None:
        raise ValueError("No embedded menu JSON found.")

    output = {
        "location": hall["name"],
        "source_url": hall["url"],
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "stations": menu["subLocations"]
    }

    path = DATA_FOLDER / f"{key}.json"

    with open(path, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    count = sum(
        len(meal.get("menuItems", []))
        for station in menu["subLocations"].values()
        for meal in station.get("mealPeriods", {}).values()
    )

    print(f"SUCCESS: Saved {path.name} ({count} menu entries)")


def main():
    failures = []

    for key, hall in DINING_HALLS.items():
        try:
            update_hall(key, hall)
        except (requests.RequestException, ValueError) as error:
            print(f"ERROR: {hall['name']}: {error}")
            failures.append(hall["name"])

    if failures:
        raise SystemExit(
            "Failed to update: " + ", ".join(failures)
        )

    print("\nAll dining halls updated successfully!")


if __name__ == "__main__":
    main()
