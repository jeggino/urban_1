import streamlit as st
import geopandas as gpd
import osmnx as ox
import folium

from streamlit_folium import st_folium



st.set_page_config(
    page_title="Urban_1",
    page_icon=":world_map:️",
    layout="wide",
)


m = folium.Map(tiles="CartoDB positron",zoom_start=1)

train_stations = ox.geometries_from_place("Amsterdam", tags={"railway":'station'}).loc["node"]
m.add_child(train_stations.explore(tooltip=["old_name:1985-2006"]))

st_data = st_folium(m, width=725)
