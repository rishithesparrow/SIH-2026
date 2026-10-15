# SIH-2026
A local-first cyclone intelligence prototype for the Indian coastline.

dea combines an interactive dashboard, historical IBTrACS cyclone tracks, and a CatBoost-based recursive forecasting model. It is designed for project demonstration and research—not as an official meteorological warning system.

Features

Historical cyclone archive for Bay of Bengal and Arabian Sea cyclones from 1990 onward

Three-hour timeline for replaying historical storm trajectories

12-hour recursive forecast at +3 h, +6 h, +9 h, and +12 h

Interactive cyclone tracker with wind, pressure, path, and intensity data

District risk, SOS-priority, and evacuation-route demonstration panels

Live current temperatures for six coastal Indian cities

Local IBTrACS archive, so historical cyclone browsing works without internet

Tech Stack

Python + Flask

Pandas, NumPy, scikit-learn, CatBoost

HTML, CSS, JavaScript, Chart.js

IBTrACS historical tropical-cyclone data

Open-Meteo for live city-temperature information

Project Structure

.
├── backend/
│   ├── app.py              # Flask server and API
│   ├── main.py             # CatBoost model and forecast logic
│   ├── ibtracs.csv         # Historical cyclone data
│   └── requirements.txt    # Python dependencies
├── frontend/
│   └── index.html          # Dashboard UI
└── README.md

Getting Started

1. Clone the repository

git clone <YOUR-REPOSITORY-URL>
cd cyclone-intelligence

2. Create and activate a virtual environment

Windows PowerShell

python -m venv .venv
.\.venv\Scripts\Activate.ps1

macOS / Linux

python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies

pip install -r backend/requirements.txt

4. Start the application

python backend/app.py

Then open:

http://127.0.0.1:5000

Do not open frontend/index.html directly or through Live Server. The cyclone archive, forecast, and live-weather controls require the Flask backend.

The first startup may take longer because the CatBoost models train when the server starts.

How to Use

Open Storm Tracker.

Select a cyclone from the historical archive.

Use the timeline slider to replay its path in three-hour intervals.

Select Run 12h Forecast to generate four future forecast points.

The solid cyan line represents observed historical data. The dotted line represents the model forecast.

API Routes

Method

Endpoint

Description

GET

/api/health

Checks whether the API is ready.

GET

/api/weather/cities

Returns live conditions for six coastal cities.

GET

/api/archive/cyclones

Lists Bay of Bengal and Arabian Sea cyclones from 1990 onward.

GET

/api/archive/cyclones/<SID>

Returns one cyclone trajectory in three-hour steps.

POST

/api/forecast

Runs the 12-hour forecast for a cyclone SID.

Model Notes

The forecasting model uses recent cyclone observations such as:

Latitude and longitude

Previous position and movement change

Wind and pressure

Wind and pressure change

Storm speed and direction

It predicts the next change in position, wind, and pressure recursively every three hours. The current horizon is limited to 12 hours because recursive uncertainty increases at longer horizons.

Limitations

This is a prototype for learning and demonstration.

It is not an official IMD, INCOIS, or government warning system.

Do not use it for real evacuation or emergency-management decisions.

District-risk, SOS, road, and shelter panels are demonstration features.

Live city weather requires internet access; the archive and forecast model remain local.

Future Improvements

Add official IMD and INCOIS advisory feeds

Include SST, humidity, wind shear, and steering-wind features

Save trained models to avoid retraining at every startup

Add authoritative district, road, shelter, and vulnerability data

Deploy the application so it can be accessed through a public URL

License
MIT license
