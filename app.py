import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import openrouteservice

st.set_page_config(layout="wide")
st.title("WasteRoute AI – Percorso su strade reali")

# ===============================
# 1) PUNTO DI PARTENZA PREDEFINITO
# ===============================
st.subheader("📍 Punto di partenza (modificabile)")

default_lat = 43.9658 # Colas Servizi, Coriano
default_lon = 12.6023

user_lat = st.number_input(
    "Latitudine (modificabile)",
    value=default_lat,
    format="%.6f"
)
user_lon = st.number_input(
    "Longitudine (modificabile)",
    value=default_lon,
    format="%.6f"
)

start_point = (user_lat, user_lon)

# ===============================
# 2) UPLOAD CSV
# ===============================
st.subheader("📂 Carica file CSV con colonne: Via, Numero, Città, Nome, Lat, Lon")
file = st.file_uploader("Carica il CSV", type=["csv"])

# ===============================
# 3) SESSION_STATE PER IL PERCORSO
# ===============================
if "route" not in st.session_state:
    st.session_state.route = None # qui salviamo le coordinate del percorso ORS

if file:
    df = pd.read_csv(file)

    # Trasforma Lat e Lon in float (gestione virgola decimale)
    df["Lat"] = df["Lat"].astype(str).str.replace(",", ".").astype(float)
    df["Lon"] = df["Lon"].astype(str).str.replace(",", ".").astype(float)

    st.subheader("📋 Punti caricati")
    st.dataframe(df)

    if not {"Lat", "Lon"}.issubset(df.columns):
        st.error("Il CSV deve contenere le colonne Lat e Lon")
        st.stop()

    # ===============================
    # 4) CREAZIONE MAPPA CON MARKER
    # ===============================
    m = folium.Map(location=start_point, zoom_start=13)

    # Marker partenza
    folium.Marker(
        start_point,
        popup="🚚 Partenza",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)

    # Marker punti
    points = []
    for _, row in df.iterrows():
        point = (row["Lat"], row["Lon"])
        points.append(point)

        folium.Marker(
            point,
            popup=f'{row["Nome"]}<br>{row["Via"]} {row["Numero"]}',
            icon=folium.Icon(color="blue", icon="trash")
        ).add_to(m)

    # ===============================
    # 5) CALCOLO PERCORSO CON ORS
    # ===============================
    ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjczMjY1YmQ4MGY2MTQ2NGQ4OWVhMzQ2N2NiNzQ4ZDMyIiwiaCI6Im11cm11cjY0In0=" # <-- Qui incolla la tua chiave ORS

    if st.button("🧭 Calcola percorso sulle strade"):
        try:
            client = openrouteservice.Client(key=ORS_API_KEY)

            # ORS richiede le coordinate in formato (lon, lat)
            coords = [(start_point[1], start_point[0])] # partenza
            for pt in points:
                coords.append((pt[1], pt[0]))

            # Richiesta ORS per il percorso su strade
            route = client.directions(
                coordinates=coords,
                profile='driving-car',
                format='geojson'
            )

            # Salva route in session_state
            st.session_state.route = route

        except Exception as e:
            st.error(f"Errore OpenRouteService: {e}")

    # ===============================
    # 6) DISEGNA ROUTE SE GIA' CALCOLATA
    # ===============================
    if st.session_state.route:
        folium.GeoJson(
            st.session_state.route,
            name="Percorso ottimizzato"
        ).add_to(m)

    # ===============================
    # 7) MOSTRA MAPPA
    # ===============================
    st_folium(m, width=1400, height=700)

else:
    st.info("Inserisci il CSV con Lat e Lon per visualizzare la mappa.")