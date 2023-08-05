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

st.pydeck_chart(pydeck_obj=r, use_container_width=True)

#---
# Creating radius buffer
# Converting CRS to a meter based CRS
train_stations.to_crs(crs=3857, inplace=True) 

# Creating 1km buffer column with WKT geometry
train_stations['buffer_geom'] = train_stations.buffer(500.0) 

# Converting back to original CRS
train_stations.to_crs(crs=4979, inplace=True) 

# Setting the geometry column to the buffer geometry
train_stations.set_geometry("buffer_geom", inplace=True)

# set name as index
train_stations.set_index("name", inplace=True)

#---
@st.cache_data
def fetch_data():
    data = ox.geometries_from_place("Amsterdam",tags={"building":True}).loc["way"]
    data.to_crs(crs=train_stations.crs, inplace=True)
    return data
 

#---
STATION = st.selectbox(label="Choose a station", options=train_stations.index.tolist(), placeholder="Select...")


try:
    building = fetch_data()
    intersected = fuel_stations[building['geometry'].intersects(train_stations.loc[STATION, 'buffer_geom'])]

    polygon = pdk.Layer(
        "PolygonLayer",
        intersected,
        stroked=True,
        get_polygon="geometry.coordinates",
        get_fill_color=[0, 0, 0, 20],
    )
    
    p = pdk.Deck(layers=[polygon])
    
    st.pydeck_chart(pydeck_obj=p, use_container_width=True)

except:
    st.warning("chose a station")
# Plottin the map to visualize
