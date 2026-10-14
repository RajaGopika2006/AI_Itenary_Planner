"""Intelligent Tourist Route Planner for Coimbatore and nearby destinations."""
from pathlib import Path
import requests
import pandas as pd
import streamlit as st

from recommendation import recommend_places
from distance import add_distances, get_travel_matrix
from route_optimizer import optimize_route

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "tourist_places_cbe.csv"

st.set_page_config(page_title="Intelligent Tourist Route Planner", page_icon="📍", layout="wide")


def get_coordinates(location_name: str):
    """Geocode a place name using OpenStreetMap Nominatim."""
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": location_name, "format": "jsonv2", "limit": 1},
        headers={"User-Agent": "TouristRoutePlanner/1.0 (educational project)"},
        timeout=15,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return None
    item = results[0]
    return {
        "latitude": float(item["lat"]),
        "longitude": float(item["lon"]),
        "display_name": item.get("display_name", location_name),
    }


@st.cache_data(show_spinner=False)
def load_places():
    df = pd.read_csv(DATA_FILE)
    required = {"name", "category", "area", "latitude", "longitude", "entry_fee", "visit_duration", "rating"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")
    for col in ("latitude", "longitude", "entry_fee", "rating"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude", "entry_fee", "rating", "name", "area"])
    df["entry_fee"] = df["entry_fee"].clip(lower=0)
    return df.reset_index(drop=True)


try:
    all_places = load_places()
except Exception as exc:
    st.error(f"Could not load the tourist places dataset: {exc}")
    st.stop()

st.title("📍 Intelligent Tourist Route Planner")
st.caption("Build a personalized sightseeing itinerary across Coimbatore, Pollachi, Valparai and Mettupalayam.")
st.info("Road distance and travel-time estimates use the public OSRM/OpenStreetMap services and require an internet connection.")

# Source selection
st.sidebar.header("📌 Starting location")
source_option = st.sidebar.radio("Choose source", ["Enter Location Manually", "Use Current Location"])
latitude = longitude = None
source_name = None

if source_option == "Enter Location Manually":
    with st.sidebar.form("location_form"):
        manual_location = st.text_input("Starting place", placeholder="Ukkadam Bus Stand, Coimbatore")
        submitted = st.form_submit_button("Find location", type="primary")
    if submitted:
        if not manual_location.strip():
            st.sidebar.warning("Enter a starting place first.")
        else:
            with st.spinner("Finding your location..."):
                try:
                    result = get_coordinates(manual_location.strip())
                    if result:
                        st.session_state["source_location"] = result
                    else:
                        st.sidebar.error("Location not found. Try a more specific place name.")
                except requests.RequestException as exc:
                    st.sidebar.error(f"Location lookup failed. Check your internet connection. Details: {exc}")
    result = st.session_state.get("source_location")
    if result:
        latitude, longitude, source_name = result["latitude"], result["longitude"], result["display_name"]
        st.sidebar.success(f"Starting point: {source_name}")
else:
    try:
        from streamlit_js_eval import get_geolocation
        geo = get_geolocation()
        if geo and isinstance(geo, dict) and "coords" in geo:
            latitude = float(geo["coords"]["latitude"])
            longitude = float(geo["coords"]["longitude"])
            source_name = "Current browser location"
            st.sidebar.success("Current location detected.")
        else:
            st.sidebar.info("Allow location access in your browser. If it does not work, choose manual location.")
    except Exception:
        st.sidebar.warning("Browser geolocation is unavailable. Please use manual location.")

if latitude is not None and longitude is not None:
    with st.expander("Starting location details", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("Latitude", f"{latitude:.6f}")
        c2.metric("Longitude", f"{longitude:.6f}")
        st.caption(source_name or "Starting location")

# Preferences
st.sidebar.header("🧭 Trip preferences")
areas = sorted(all_places["area"].astype(str).unique().tolist())
start_area = st.sidebar.selectbox("Preferred area", ["All Areas"] + areas)
available_time = st.sidebar.slider("Available time (hours)", 1, 24, 6)
budget = st.sidebar.number_input("Total entry-fee budget (₹)", min_value=0, max_value=100000, value=1000, step=100)
categories = sorted(all_places["category"].dropna().astype(str).unique().tolist())
interests = st.sidebar.multiselect("Interests", categories, help="Leave empty to consider all categories.")
max_places = st.sidebar.slider("Maximum places to visit", 1, 10, 3)

st.subheader("Your trip preferences")
c1, c2, c3 = st.columns(3)
c1.metric("Preferred area", start_area)
c2.metric("Available time", f"{available_time} hours")
c3.metric("Entry-fee budget", f"₹{budget:,.0f}")

# Recommendations
st.subheader("⭐ Recommended tourist places")
recommended = recommend_places(
    str(DATA_FILE), start_area, interests, budget, available_time,
    max_places=max_places, candidate_pool_size=min(15, max_places * 2)
)
if recommended.empty:
    st.warning("No places matched the selected area. Try All Areas or another area.")
    st.stop()

show_cols = [c for c in ["name", "area", "category", "entry_fee", "visit_duration", "rating", "recommendation_score", "description"] if c in recommended.columns]
st.dataframe(recommended[show_cols], use_container_width=True, hide_index=True)

# Road distance table is optional; keep recommendations useful if routing service is down.
if latitude is not None and longitude is not None:
    st.subheader("🚗 Road distance from your starting point")
    try:
        with st.spinner("Calculating road distances..."):
            distance_df = add_distances(recommended, latitude, longitude)
        st.dataframe(
            distance_df[[c for c in ["name", "area", "distance_km", "travel_time_minutes", "rating"] if c in distance_df.columns]]
                .sort_values("distance_km", na_position="last"),
            use_container_width=True, hide_index=True,
        )
    except Exception as exc:
        st.warning(f"Road-distance lookup is temporarily unavailable. Recommendations are still shown. Details: {exc}")

st.subheader("🗺️ Optimized itinerary")
if latitude is None or longitude is None:
    st.info("Set a starting location above to calculate travel times and build an optimized route.")
else:
    try:
        with st.spinner("Optimizing your route..."):
            # A manageable candidate pool makes route optimization faster and respects user interests.
            travel_data = get_travel_matrix(recommended, latitude, longitude)
            optimized = optimize_route(recommended, travel_data["durations"], available_time, max_places, budget)
        if optimized is None:
            st.warning("No feasible itinerary was found within your selected time and entry-fee budget. Try increasing the time/budget or reducing visit duration expectations.")
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("Places in route", len(optimized["route"]))
            m2.metric("Estimated time", f"{optimized['total_time_minutes'] // 60} h {optimized['total_time_minutes'] % 60} min")
            m3.metric("Total entry fees", f"₹{optimized['total_fee']:,.0f}")
            st.caption("Estimated time includes road travel and each place's listed visit duration. Traffic, opening hours and waiting time may change the actual trip.")
            for number, place in enumerate(optimized["route"], start=1):
                with st.container(border=True):
                    st.markdown(f"**{number}. {place['name']}**")
                    st.write(f"{place['area']} · {place['category']} · Rating: {place['rating']}/5")
                    st.write(f"Visit duration: {place['visit_duration']} · Entry fee: ₹{float(place['entry_fee']):,.0f}")
                    if "description" in place and pd.notna(place["description"]):
                        st.write(place["description"])
                    query = requests.utils.quote(f"{place['name']} {place['area']} Tamil Nadu")
                    st.markdown(f"[Open in Google Maps](https://www.google.com/maps/search/?api=1&query={query})")
    except Exception as exc:
        st.error("Could not calculate the optimized route right now. Check your internet connection and try again.")
        st.caption(f"Technical details: {exc}")

st.divider()
st.caption("Project note: This is an educational route-planning prototype. Confirm opening hours, entry fees and road conditions before travelling.")
