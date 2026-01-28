from pathlib import Path
import streamlit as st
import base64
import pandas as pd
import maptoposter.create_map_poster as mp
import os
#from loguru import logger
import time
import osmnx as ox
from utils import plot_everything

# logger.add("mein_log_file.log", rotation="1 MB", level="INFO")

def find_first_file(folder: str | Path, search_term: str, pattern="*"):
    folder = Path(folder)

    for file in folder.iterdir():  # nur dieser Ordner, nicht rekursiv
        if file.is_file() and search_term in file.name:
            return file
    return None

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        print(e)
        return None

@st.cache_data
def get_coordinates_cached(city, country):
    return mp.get_coordinates(city, country)

st.header("Your City as a Poster")


tab1, tab2, tab3 = st.tabs(["Coordinates", "Themes", "Settings"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        CITY = st.text_input("City:")
    with col2:
        COUNTRY = st.text_input("Country:")

    if CITY and COUNTRY:
        try:
            COORDS = get_coordinates_cached(CITY, COUNTRY)
            st.caption(f"{CITY}, {COUNTRY} has the coordinates {COORDS[0]}° N / {COORDS[1]}° E")
        except ValueError as e:
            st.error(e)

    else:
        st.warning("Please enter City and Country")

with tab2:

    themes = mp.get_available_themes()
    # st.write(themes)
    theme = st.selectbox("Select Theme", themes)
    THEME = mp.load_theme(theme)
    mp.THEME = THEME

    thumb_dir = "maptoposter/posters/thumbs"
    df = pd.DataFrame({"Theme": themes})
    files = os.listdir(thumb_dir)

    def find_thumbnail(theme_name):
        # Sucht die erste Datei, die das Theme im Namen trägt
        for f in files:
            if theme_name.lower() in f.lower():
                return os.path.join(thumb_dir, f)
        return None  # Falls nichts gefunden wurde


    # 4. Spalte im DataFrame erstellen
    df["Path"] = df["Theme"].apply(find_thumbnail)

    df["Bild"] = df["Path"].apply(get_image_base64)
    df = df.sort_values(by=["Theme"])

    st.dataframe(
        df[["Bild", "Theme"]],  # Nur die relevanten Spalten anzeigen
        column_config={
            "Bild": st.column_config.ImageColumn(
                label="Vorschau",
                width=40,)
        },
        hide_index=True,
        row_height=300,

    )

    # st.dataframe(df)

with tab3:
    radius = st.number_input("select Radius",
                             min_value=500,
                             max_value=20000,
                             value=2000,
                             step=500)

    network = st.selectbox("Network", ["all", "all_public", "bike", "drive", "walk"])
    dpi = st.number_input("DPI", value=300, step=50)



run = st.button("Run")
if run:
    output_file_name = mp.generate_output_filename(CITY, theme)
    start = time.time()
    # with st.spinner("Creating Poster...", show_time=True):
    with st.status("Creating Citymap..", expanded=True) as status:
        status.write("Downloading street data..")
        G = ox.graph_from_point(COORDS, dist=radius, dist_type="bbox", network_type=network)
        time.sleep(0.5)
        try:
            status.write("Downloading water data...")
            # status.update(label="Lade Gewässer...", state="running")
            water = ox.features_from_point(COORDS, tags={'natural': 'water', 'waterway': 'riverbank'}, dist=radius)
        except:
            water = None
        time.sleep(0.3)

        try:
            status.write("Downloading green space data...")
            # status.update(label="Lade Gewässer...", state="running")
            parks = ox.features_from_point(COORDS, tags={'leisure': 'park', 'landuse': 'grass'}, dist=radius)
        except:
            parks = None

        status.write("Rendering map data...")
        # status.update(label="Erstelle Poster-Design...", state="running")
        image_data = plot_everything(G=G, water=water, parks=parks, THEME=THEME, city=CITY, country=COUNTRY, point=COORDS)
        status.update(label="Citymap successfully completed!", state="complete", expanded=False)
    #logger.info(f"Radius: {radius} took: {time.time()-start}"),
    st.image(image_data, caption=f"Picture for {CITY}, {COUNTRY}")
    #st.write(output_file_name)##

    st.download_button(
        label="Download Poster",
        data=image_data,  # Hier wird das geöffnete File-Objekt übergeben
        file_name=f"{CITY}_{theme}_{int(time.time())}.png",
        mime="image/png"
    )