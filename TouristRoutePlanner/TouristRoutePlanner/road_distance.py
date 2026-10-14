import requests


OSRM_URL = "https://router.project-osrm.org"


def get_road_distance_and_time(
    start_lat,
    start_lon,
    end_lat,
    end_lon
):

    coordinates = (
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
    )

    url = f"{OSRM_URL}/route/v1/driving/{coordinates}"

    params = {
        "overview": "false"
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if data["code"] != "Ok":
        raise ValueError(
            f"OSRM routing error: {data['code']}"
        )

    route = data["routes"][0]

    distance_km = route["distance"] / 1000
    travel_time_minutes = route["duration"] / 60

    return {
        "distance_km": round(distance_km, 2),
        "travel_time_minutes": round(travel_time_minutes)
    }

def add_road_distance(
    df,
    source_lat,
    source_lon
):

    df = df.copy()

    distances = []
    travel_times = []

    for _, row in df.iterrows():

        try:
            result = get_road_distance_and_time(
                source_lat,
                source_lon,
                row["latitude"],
                row["longitude"]
            )

            distances.append(
                result["distance_km"]
            )

            travel_times.append(
                result["travel_time_minutes"]
            )

        except Exception:
            distances.append(None)
            travel_times.append(None)

    df["road_distance_km"] = distances
    df["travel_time_minutes"] = travel_times

    return df