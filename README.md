Intelligent Tourist Route Planner

A Streamlit application that recommends tourist places around Coimbatore, Pollachi, Valparai and Mettupalayam, then attempts to build a time- and budget-aware itinerary using road travel estimates.
Features

    Manual starting-place search using OpenStreetMap Nominatim
    Optional browser geolocation (requires browser permission and a supported context)
    Tourist-place dataset loaded from the project folder
    Recommendations based on area, interests, ratings, entry fees and visit time
    Road distance and travel-time estimates using the public OSRM routing service
    Route optimization constrained by available time, entry-fee budget and maximum number of places
    Google Maps links for itinerary stops

Requirements

    Python 3.10 or newer
    Internet connection for geocoding and road-routing requests
    A modern browser for Streamlit

Run on Windows

    Extract the ZIP file.

    Open Command Prompt or PowerShell in the extracted TouristRoutePlanner folder (the folder containing app.py).

    Create and activate a virtual environment:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1

    If PowerShell blocks activation, run \.venv\Scripts\python.exe -m pip ... directly or use Command Prompt and .venv\Scripts\activate.bat.

    Install dependencies:

    python -m pip install --upgrade pip
    pip install -r requirements.txt

    Start the app:

    streamlit run app.py

    Streamlit opens a local browser page. Use Enter Location Manually first if browser geolocation is unavailable.

Run on Linux / macOS

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py

Project files

    app.py — Streamlit interface and application flow
    recommendation.py — preference scoring and visit-duration parsing
    distance.py — OSRM road distance and travel-time matrix calls
    road_distance.py — direct point-to-point OSRM helper retained for standalone use
    route_optimizer.py — time/budget-constrained route search
    location.py — legacy browser-location helper retained for reference
    tourist_places_cbe.csv — tourist-place dataset

Notes and limitations

    Public Nominatim and OSRM endpoints are community services. They may rate-limit requests or be temporarily unavailable; this project is not intended for high-volume production traffic.
    Entry fees, ratings, descriptions and visit durations come from the included CSV and should be verified before travel.
    The optimizer uses the listed visit durations and road travel durations. It does not currently enforce attraction opening/closing times, meal breaks, parking, or live traffic.
    Browser geolocation requires permission. If it fails, use manual location.
