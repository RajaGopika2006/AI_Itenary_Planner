"""Road-distance and travel-time matrix helpers using the public OSRM demo server."""
import requests

OSRM_URL = "https://router.project-osrm.org"


def _get_table(coordinates, sources=None, destinations=None):
    if len(coordinates) < 2:
        raise ValueError("At least two coordinates are required.")
    url = f"{OSRM_URL}/table/v1/driving/" + ";".join(coordinates)
    params = {"annotations": "distance,duration"}
    if sources is not None:
        params["sources"] = sources
    if destinations is not None:
        params["destinations"] = destinations
    response = requests.get(url, params=params, timeout=45)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "Ok":
        raise ValueError(f"OSRM routing error: {data.get('code', 'unknown error')}")
    return data


def _coordinates(df, source_lat=None, source_lon=None):
    coords = []
    if source_lat is not None and source_lon is not None:
        coords.append(f"{float(source_lon)},{float(source_lat)}")
    for _, row in df.iterrows():
        coords.append(f"{float(row['longitude'])},{float(row['latitude'])}")
    return coords


def add_distances(df, source_lat, source_lon):
    result = df.copy()
    coordinates = _coordinates(result, source_lat, source_lon)
    data = _get_table(coordinates, sources="0", destinations=";".join(map(str, range(1, len(coordinates)))))
    distances = data["distances"][0]
    durations = data["durations"][0]
    result["distance_km"] = [round(v / 1000, 2) if v is not None else None for v in distances]
    result["travel_time_minutes"] = [round(v / 60) if v is not None else None for v in durations]
    return result


def get_travel_matrix(df, source_lat, source_lon):
    coordinates = _coordinates(df, source_lat, source_lon)
    data = _get_table(coordinates)
    return {"durations": data["durations"], "distances": data["distances"]}
