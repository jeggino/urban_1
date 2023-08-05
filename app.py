import streamlit as st
import geopandas as gpd
import osmnx as ox
import pydeck as pdk



st.set_page_config(
    page_title="Urban_1",
    page_icon=":world_map:️",
    layout="wide",
)



train_stations = ox.geometries_from_place("Amsterdam", tags={"railway":'station'}).loc["node"]


# Define a layer to display on a map
layer = pdk.Layer(
    "ScatterplotLayer",
    train_stations,
    pickable=True,
    opacity=0.8,
    stroked=True,
    filled=True,
    radius_scale=3,
    radius_min_pixels=1,
    radius_max_pixels=100,
    line_width_min_pixels=1,
    get_position="geometry.coordinates",
    get_radius=100,
    get_fill_color=[255, 140, 0],
    get_line_color=[0, 0, 0],
)

r = pdk.Deck(layers=[layer],tooltip={"text": "{name}"})

st.pydeck_chart(pydeck_obj=f, use_container_width=True)
