/* Frontend for the Flask API in ../main.py. Only backend-supported features are rendered. */
const API_BASE = "http://127.0.0.1:5000/api";
const maps = {};
const layers = { simulation: null, archive: null };
let latestSimulation = null;
let settlements = [];
let archiveCyclone = null;
let archiveIndex = 0;
let playbackTimer = null;
let archiveComparison = null;
let selectedStartMarker = null;
let activeCyclones = [];

const WEATHER_CITIES = [
  { name: "Chennai", state: "Tamil Nadu", lat: 13.083, lon: 80.271 },
  { name: "Visakhapatnam", state: "Andhra Pradesh", lat: 17.687, lon: 83.218 },
  { name: "Bhubaneswar", state: "Odisha", lat: 20.296, lon: 85.825 },
  { name: "Kolkata", state: "West Bengal", lat: 22.573, lon: 88.364 },
  { name: "Mumbai", state: "Maharashtra", lat: 19.076, lon: 72.878 },
];

const $ = (selector) => document.querySelector(selector);
const number = (value, digits = 1) => Number(value).toFixed(digits);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", '"':"&quot;" }[character]));

function makeMap(id) {
  const map = L.map(id, { zoomControl: false }).setView([15, 85], 5);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "© OpenStreetMap contributors",
  }).addTo(map);
  maps[id] = map;
  return map;
}

function selectSimulationStart(event) {
  const { lat, lng } = event.latlng;
  // Keep map-picked coordinates consistent with the two-decimal simulator inputs.
  $("#simulationForm [name='lat']").value = lat.toFixed(2);
  $("#simulationForm [name='lon']").value = lng.toFixed(2);
  if (selectedStartMarker) selectedStartMarker.remove();
  selectedStartMarker = L.circleMarker([lat, lng], { radius: 7, color: "#43d5d3", fillColor: "#43d5d3", fillOpacity: 1, weight: 2 })
    .bindTooltip("Selected simulation start").addTo(maps.simulationMap);
  $("#simulationMapMessage").textContent = `Selected ${lat.toFixed(2)}, ${lng.toFixed(2)}`;
}

function setSimulationStartTimeToNow() {
  const input = $("#simulationForm [name='startTime']");
  const now = new Date();
  // datetime-local expects a local clock value, while toISOString is UTC.
  const localNow = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  input.value = localNow.toISOString().slice(0, 16);
}

async function loadWeather() {
  const target = $("#weatherCards");
  try {
    const reports = await Promise.all(WEATHER_CITIES.map(async (city) => {
      const params = new URLSearchParams({ latitude: city.lat, longitude: city.lon, current: "temperature_2m", hourly: "precipitation_probability", timezone: "auto", forecast_days: "1" });
      const data = await fetch(`https://api.open-meteo.com/v1/forecast?${params}`).then((response) => {
        if (!response.ok) throw new Error("Weather service unavailable");
        return response.json();
      });
      const index = Math.max(0, data.hourly.time.findIndex((time) => time.slice(0, 13) === data.current.time.slice(0, 13)));
      return { ...city, temperature: data.current.temperature_2m, rainProbability: data.hourly.precipitation_probability[index], time: data.current.time };
    }));
    target.innerHTML = reports.map((city) => `<article class="weather-card"><h3>${escapeHtml(city.name)}</h3><p>${escapeHtml(city.state)} · ${escapeHtml(city.time.replace("T", " "))}</p><div class="weather-reading"><b>${number(city.temperature)}°C</b><span>Rain chance<br><strong>${city.rainProbability}%</strong></span></div></article>`).join("");
  } catch (error) {
    target.innerHTML = '<div class="empty-state">Live weather is temporarily unavailable. Refresh to try again.</div>';
  }
}

function renderActiveCyclones(data) {
  const target = $("#activeCyclones");
  activeCyclones = data.cyclones || [];
  $("#activeCycloneStatus").textContent = data.sourceNotice || "Active observations loaded.";
  if (!activeCyclones.length) {
    target.innerHTML = '<div class="empty-state">No active cyclone observations are currently available for the Bay of Bengal or Arabian Sea.</div>';
    return;
  }
  target.innerHTML = activeCyclones.map((cyclone, index) => `<article class="active-cyclone-card"><h3>${escapeHtml(cyclone.name)}</h3><p>${escapeHtml(cyclone.subbasin)} · observed ${escapeHtml(cyclone.observedAt.replace("T", " "))}</p><div class="active-cyclone-metrics"><div><small>POSITION</small><b>${number(cyclone.lat, 2)}, ${number(cyclone.lon, 2)}</b></div><div><small>WIND</small><b>${number(cyclone.wind)} kt</b></div><div><small>PRESSURE</small><b>${number(cyclone.pressure)} hPa</b></div><div><small>MOVEMENT</small><b>${number(cyclone.stormSpeed)} kt / ${number(cyclone.stormDirection)}°</b></div></div><button class="primary-button" type="button" data-active-index="${index}">Predict next 12 hours <span>→</span></button></article>`).join("");
  target.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => predictActiveCyclone(activeCyclones[Number(button.dataset.activeIndex)], button)));
}

async function loadActiveCyclones() {
  const target = $("#activeCyclones");
  $("#activeCycloneStatus").textContent = "Checking active North Indian Ocean observations…";
  target.innerHTML = '<div class="empty-state">Loading active cyclone data…</div>';
  try { renderActiveCyclones(await api("/live-cyclones")); }
  catch (error) {
    // Keep the dashboard wording simple when the live source has no usable result.
    $("#activeCycloneStatus").textContent = "No active cyclones as of now.";
    target.innerHTML = '<div class="empty-state">No active cyclones as of now in the Bay of Bengal or Arabian Sea.</div>';
  }
}

async function predictActiveCyclone(cyclone, button) {
  button.disabled = true; button.textContent = "Starting prediction…";
  try {
    const data = await api("/forecast", { method: "POST", body: JSON.stringify({ ...cyclone.simulationInput, startTime: cyclone.observedAt }) });
    latestSimulation = data;
    const current = cyclone.simulationInput.current;
    $("#simulationForm [name='lat']").value = current.lat;
    $("#simulationForm [name='lon']").value = current.lon;
    $("#simulationForm [name='wind']").value = current.wind;
    $("#simulationForm [name='pressure']").value = current.pressure;
    $("#simulationForm [name='stormSpeed']").value = current.stormSpeed;
    $("#simulationForm [name='stormDirection']").value = current.stormDirection;
    $("#rankRiskButton").disabled = settlements.length === 0;
    renderSimulation(data);
    $("#simulator").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) { $("#simulationMapMessage").textContent = "Live prediction unavailable"; showError($("#simulationResult"), error.message); }
  finally { button.disabled = false; button.innerHTML = "Predict next 12 hours <span>→</span>"; }
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || "The backend could not complete this request.");
  return body;
}

function showError(target, message) {
  target.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function clearLayer(name) {
  if (layers[name]) layers[name].clearLayers();
  else layers[name] = L.layerGroup().addTo(maps[`${name}Map`]);
  return layers[name];
}

function colorForRisk(level) {
  return ({ Red: "#f15862", Orange: "#f58b3c", Yellow: "#f2bf4c", Green: "#4de197" })[level] || "#43d5d3";
}

function pointPopup(point, title) {
  return `<b>${title}</b><br>+${point.forecastHour || 0} h · ${escapeHtml(point.timestamp || "start")}`
    + `<br>Lat ${number(point.lat, 3)} · Lon ${number(point.lon, 3)}`
    + `<br>Wind ${number(point.wind)} kt · Pressure ${number(point.pressure)} hPa`
    + `<br>Speed ${number(point.stormSpeed)} kt · Direction ${number(point.stormDirection)}°`;
}

function renderSimulation(data) {
  const group = clearLayer("simulation");
  const trajectory = data.trajectory;
  const coordinates = trajectory.map((point) => [point.lat, point.lon]);
  L.polyline(coordinates, { color: "#43d5d3", weight: 3, dashArray: "8 7" }).addTo(group);
  L.marker(coordinates[0]).bindPopup(pointPopup(data.origin, "Simulation origin")).addTo(group);

  data.points.forEach((point) => {
    L.circleMarker([point.lat, point.lon], { radius: 6, color: "#43d5d3", fillColor: "#08111f", fillOpacity: 1, weight: 2 })
      .bindPopup(pointPopup(point, "Model prediction")).addTo(group);
  });
  data.uncertaintyCorridor.forEach((circle) => {
    L.circle([circle.center.lat, circle.center.lon], { radius: circle.radiusKm * 1000, color: "#43d5d3", weight: 1, fillColor: "#43d5d3", fillOpacity: .045, interactive: false }).addTo(group);
  });
  data.impactCorridor.forEach((circle) => {
    L.circle([circle.center.lat, circle.center.lon], { radius: circle.impactRadiusKm * 1000, color: colorForRisk(circle.riskLevel), weight: 1, opacity: .5, fillColor: colorForRisk(circle.riskLevel), fillOpacity: .035, interactive: false }).addTo(group);
  });
  maps.simulationMap.fitBounds(coordinates, { padding: [35, 35], maxZoom: 7 });
  $("#simulationMapMessage").textContent = "Forecast loaded";

  $("#simulationResult").innerHTML = `<div class="forecast-grid">${data.points.map((point) => `
    <article class="forecast-card"><h3>+${point.forecastHour} HOURS</h3><b>${number(point.wind)} <small>kt</small></b>
      <p>Lat ${number(point.lat, 3)} · Lon ${number(point.lon, 3)}</p><p>${number(point.pressure)} hPa · ${number(point.stormSpeed)} kt / ${number(point.stormDirection)}°</p>
      <p>Uncertainty radius: ±${number(point.uncertaintyKm)} km</p></article>`).join("")}</div>
    <p class="notice">${escapeHtml(data.notice)} Movement source: ${escapeHtml(data.origin.startingMovementSource || "provided state")}.</p>`;
}

async function runSimulation(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const button = event.currentTarget.querySelector("button");
  button.disabled = true; button.textContent = "Running simulation…";
  $("#simulationMapMessage").textContent = "Calling model…";
  try {
    const startTime = form.get("startTime");
    const data = await api("/forecast", { method: "POST", body: JSON.stringify({ current: {
      lat: Number(form.get("lat")), lon: Number(form.get("lon")), wind: Number(form.get("wind")), pressure: Number(form.get("pressure")),
      stormSpeed: Number(form.get("stormSpeed")), stormDirection: Number(form.get("stormDirection")),
    }, ...(startTime ? { startTime } : {}) }) });
    latestSimulation = data;
    $("#rankRiskButton").disabled = settlements.length === 0;
    renderSimulation(data);
  } catch (error) {
    $("#simulationMapMessage").textContent = "Simulation unavailable";
    showError($("#simulationResult"), error.message);
  } finally { button.disabled = false; button.innerHTML = "Run 12-hour simulation <span>→</span>"; }
}

function renderArchiveList(cyclones) {
  const list = $("#archiveList");
  if (!cyclones.length) { list.innerHTML = '<p class="muted">No matching cyclones found.</p>'; return; }
  list.innerHTML = cyclones.map((cyclone) => `<button class="archive-item" data-sid="${escapeHtml(cyclone.sid)}"><b>${escapeHtml(cyclone.name)}</b><small>${cyclone.season} · ${escapeHtml(cyclone.subbasin)} · ${cyclone.observations} observations</small></button>`).join("");
  list.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => loadArchive(button.dataset.sid, button)));
}

async function searchArchive() {
  const params = new URLSearchParams({ limit: "100" });
  if ($("#archiveName").value.trim()) params.set("name", $("#archiveName").value.trim());
  if ($("#archiveYear").value.trim()) params.set("year", $("#archiveYear").value.trim());
  $("#archiveList").innerHTML = '<p class="muted">Loading archive…</p>';
  try { renderArchiveList((await api(`/archive/cyclones?${params}`)).cyclones); }
  catch (error) { showError($("#archiveList"), error.message); }
}

async function loadArchive(sid, button) {
  try {
    archiveCyclone = (await api(`/archive/cyclones/${encodeURIComponent(sid)}`)).cyclone;
    archiveIndex = 0;
    archiveComparison = null;
    $("#archiveList").querySelectorAll("button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    $("#archiveTitle").textContent = `${archiveCyclone.name} · ${archiveCyclone.season}`;
    $("#archiveSlider").max = archiveCyclone.points.length - 1;
    $("#archiveSlider").value = 0;
    $("#archiveSlider").disabled = false;
    renderArchiveTrack();
  } catch (error) { showError($("#comparisonResult"), error.message); }
}

function renderArchiveTrack() {
  if (!archiveCyclone) return;
  const group = clearLayer("archive");
  const points = archiveCyclone.points;
  const coordinates = points.map((point) => [point.lat, point.lon]);
  L.polyline(coordinates, { color: "#91a3be", weight: 2 }).addTo(group);
  L.polyline(coordinates.slice(0, archiveIndex + 1), { color: "#43d5d3", weight: 3 }).addTo(group);
  if (archiveComparison && archiveComparison.pointIndex === archiveIndex) {
    const actualCoordinates = archiveComparison.actualTrajectory.map((item) => [item.lat, item.lon]);
    const predictedCoordinates = archiveComparison.predictedTrajectory.map((item) => [item.lat, item.lon]);
    L.polyline(actualCoordinates, { color: "#43d5d3", weight: 5, opacity: .8 }).bindTooltip("Actual historical path").addTo(group);
    L.polyline(predictedCoordinates, { color: "#f58b3c", weight: 4, dashArray: "8 7" }).bindTooltip("Model prediction").addTo(group);
    archiveComparison.predictedTrajectory.slice(1).forEach((item) => {
      L.circle([item.lat, item.lon], { radius: item.uncertaintyKm * 1000, color: "#f58b3c", weight: 1, fillColor: "#f58b3c", fillOpacity: .045, interactive: false }).addTo(group);
      L.circleMarker([item.lat, item.lon], { radius: 5, color: "#f58b3c", fillColor: "#08111f", fillOpacity: 1, weight: 2 })
        .bindPopup(pointPopup(item, "Model prediction")).addTo(group);
    });
  }
  const point = points[archiveIndex];
  L.circleMarker([point.lat, point.lon], { radius: 8, color: "#43d5d3", fillColor: "#43d5d3", fillOpacity: 1 }).bindPopup(pointPopup(point, "Historical observation")).addTo(group);
  maps.archiveMap.fitBounds(coordinates, { padding: [30, 30], maxZoom: 7 });
  $("#archiveTimestamp").textContent = point.timestamp.replace("T", " ");
  $("#archivePointText").textContent = `${archiveIndex + 1} / ${points.length}`;
  $("#archiveVitals").innerHTML = `
    <div><small>LAT / LON</small><b>${number(point.lat, 2)} / ${number(point.lon, 2)}</b></div>
    <div><small>WIND</small><b>${number(point.wind)} kt</b></div>
    <div><small>PRESSURE</small><b>${number(point.pressure)} hPa</b></div>
    <div><small>MOVEMENT</small><b>${number(point.stormSpeed)} kt / ${number(point.stormDirection)}°</b></div>`;
  const validComparisonIndex = archiveIndex >= 2 && archiveIndex <= points.length - 5;
  $("#compareButton").disabled = !validComparisonIndex;
  $("#compareHelp").textContent = validComparisonIndex
    ? "Runs a 12-hour prediction from this observation and compares it with real data."
    : "Move to a point with two earlier and four later observations for a 12-hour comparison.";
}

function togglePlayback() {
  if (!archiveCyclone) return;
  if (playbackTimer) { clearInterval(playbackTimer); playbackTimer = null; $("#archivePlay").textContent = "▶"; return; }
  playbackTimer = setInterval(() => {
    archiveIndex = archiveIndex >= archiveCyclone.points.length - 1 ? 0 : archiveIndex + 1;
    $("#archiveSlider").value = archiveIndex; renderArchiveTrack();
  }, 750);
  $("#archivePlay").textContent = "❚❚";
}

async function compareHistoricalSimulation() {
  if (!archiveCyclone) return;
  const target = $("#comparisonResult");
  target.innerHTML = '<div class="empty-state">Running the historical model comparison…</div>';
  try {
    const data = await api(`/archive/cyclones/${encodeURIComponent(archiveCyclone.sid)}/simulation-comparison?pointIndex=${archiveIndex}`);
    archiveComparison = data;
    renderArchiveTrack();
    target.innerHTML = `<div class="comparison-summary"><div><small>MEAN TRACK ERROR</small><b>${number(data.summary.meanTrackErrorKm)} km</b></div><div><small>MEAN WIND ERROR</small><b>${number(data.summary.meanWindErrorKt)} kt</b></div><div><small>MEAN PRESSURE ERROR</small><b>${number(data.summary.meanPressureErrorHpa)} hPa</b></div></div>
      <table class="comparison-table"><thead><tr><th>Horizon</th><th>Actual position</th><th>Predicted position</th><th>Track error</th><th>Wind error</th></tr></thead><tbody>${data.comparison.map((row) => `<tr><td>+${row.forecastHour} h</td><td>${number(row.actual.lat, 2)}, ${number(row.actual.lon, 2)}</td><td>${number(row.predicted.lat, 2)}, ${number(row.predicted.lon, 2)}</td><td>${number(row.trackErrorKm)} km</td><td>${number(row.windErrorKt)} kt</td></tr>`).join("")}</tbody></table><p class="notice">${escapeHtml(data.notice)}</p>`;
  } catch (error) { showError(target, error.message); }
}

function renderSettlementChips() {
  const target = $("#settlementChips");
  if (!settlements.length) { target.innerHTML = '<p class="muted">No areas added yet.</p>'; return; }
  target.innerHTML = settlements.map((place, index) => `<div class="settlement-chip"><span>${escapeHtml(place.area)} · ${number(place.lat, 2)}, ${number(place.lon, 2)}</span><button type="button" data-index="${index}" aria-label="Remove ${escapeHtml(place.area)}">×</button></div>`).join("");
  target.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => { settlements.splice(Number(button.dataset.index), 1); renderSettlementChips(); $("#rankRiskButton").disabled = !latestSimulation || !settlements.length; }));
}

function addSettlement(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  settlements.push({ area: form.get("area").trim(), lat: Number(form.get("lat")), lon: Number(form.get("lon")) });
  event.currentTarget.reset(); renderSettlementChips(); $("#rankRiskButton").disabled = !latestSimulation;
}

async function rankRisk() {
  const target = $("#riskResult");
  if (!latestSimulation || !settlements.length) return;
  target.innerHTML = '<div class="empty-state">Calculating transparent prototype risk scores…</div>';
  try {
    const data = await api("/risk/rank", { method: "POST", body: JSON.stringify({ forecast: latestSimulation.points, settlements }) });
    target.innerHTML = data.rankings.map((item, index) => `<div class="risk-row"><span class="risk-rank">${String(index + 1).padStart(2, "0")}</span><div><b>${escapeHtml(item.area)}</b><small>${number(item.closestDistanceKm)} km from path</small></div><div><span class="risk-level level-${item.riskLevel.toLowerCase()}">${item.riskLevel}</span><small>${item.priority} priority</small></div><div><b>${number(item.riskScore)} / 100</b><small>risk score</small></div><div><b>${item.estimatedClosestApproach}</b><small>${number(item.predictedWindAtClosestApproach)} kt wind</small></div></div>`).join("") + (data.notice ? `<p class="notice">${escapeHtml(data.notice)}</p>` : "");
  } catch (error) { showError(target, error.message); }
}

async function checkBackend() {
  try { await api("/health"); const status = $("#apiStatus"); status.textContent = "Backend online"; status.className = "api-status ok"; }
  catch (_) { const status = $("#apiStatus"); status.textContent = "Backend offline"; status.className = "api-status error"; }
}

function initialise() {
  makeMap("simulationMap"); makeMap("archiveMap");
  maps.simulationMap.on("click", selectSimulationStart);
  setSimulationStartTimeToNow();
  $("#useCurrentTime").addEventListener("click", setSimulationStartTimeToNow);
  $("#simulationForm").addEventListener("submit", runSimulation);
  $("#refreshActiveCyclones").addEventListener("click", loadActiveCyclones);
  $("#archiveSearch").addEventListener("click", searchArchive);
  $("#archiveName").addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); searchArchive(); } });
  $("#archiveYear").addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); searchArchive(); } });
  $("#archiveSlider").addEventListener("input", (event) => { archiveIndex = Number(event.target.value); renderArchiveTrack(); });
  $("#archivePlay").addEventListener("click", togglePlayback);
  $("#compareButton").addEventListener("click", compareHistoricalSimulation);
  $("#settlementForm").addEventListener("submit", addSettlement);
  $("#rankRiskButton").addEventListener("click", rankRisk);
  checkBackend();
  loadWeather();
  loadActiveCyclones();
}

initialise();
