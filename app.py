import streamlit as st
import pandas as pd
import geopandas as gpd
import osmnx as ox
import seaborn as sns
import pydeck as pdk


#----------------------------------------------------------------
st.set_page_config(
    page_title="Urban_1",
    page_icon=":world_map:️",
    layout="wide",
)

#----------------------------------------------------------------
@st.cache_data
def data_buildings():
    df = pd.DataFrame()
    for i in range(10):
        gdf = gpd.read_file(f'buildings_{i}.geojson')
        df = pd.concat([df, gdf], ignore_index=True)
    return df

@st.cache_data
def data():
    buildings = data_buildings()
    train_stations = gpd.read_file(f'train_stations.geojson')
    return buildings, train_stations


buildings = data()[0]
train_stations = data()[1]

#----------------------------------------------------------------
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

#----------------------------------------------------------------
station = st.selectbox(label="Chose a station", options=train_stations.index, label_visibility="visible")

buildings.to_crs(crs=train_stations.crs, inplace=True) 
intersected = buildings[buildings['geometry'].intersects(train_stations.loc[station, 'buffer_geom'])]

df_WONINGWAARDE_2022 = gpd.read_file("https://maps.amsterdam.nl/open_geodata/geojson_lnglat.php?KAARTLAAG=WONINGWAARDE_2022&THEMA=woningwaarde")

df_join = gpd.sjoin(intersected, df_WONINGWAARDE_2022.to_crs(intersected.crs))

#----------------------------------------------------------------
ICON_URL = "https://th.bing.com/th/id/R.210d1413e803794de617b1e6c6eddcdb?rik=NGXB8Kb60FgrQw&riu=http%3a%2f%2fclipart-library.com%2fimages_k%2ftrain-silhouette-png%2ftrain-silhouette-png-21.png&ehk=s0elGcYU9ZR3Pim0iQnF1SN4VEJDXP0GxwFvqF4SHtY%3d&risl=&pid=ImgRaw&r=0"

icon_data = {
    "url": ICON_URL,
    "width": 242,
    "height": 142,
    "anchorY": 0,
}

data = train_stations.loc[station]
data["icon_data"] = icon_data
data = data.to_frame().T[["geometry","icon_data"]].reset_index()
data = gpd.GeoDataFrame(data,geometry='geometry',crs=4979)


icon_layer = pdk.Layer(
    type="IconLayer",
    data=data,
    get_icon="icon_data",
    size_scale=30,
    get_position=[train_stations.loc[station].geometry.x, 
                  train_stations.loc[station].geometry.y],
    # pickable=True,
)


#----------------------------------------------------------------
colors = dict(zip(df_join.LABEL.sort_values().unique().tolist(),
                  list(sns.color_palette("husl", 
                                         len(df_join.LABEL.sort_values().unique())))))
df_polygons = df_join[["geometry","LABEL"]]
df_polygons['color'] = df_polygons["LABEL"].map(colors).apply(lambda x: [i*255 for i in x])
df_polygons.to_crs(crs=4979, inplace=True) 

polygon_layer = pdk.Layer("GeoJsonLayer", 
    data=df_polygons, 
    get_fill_color='color',
    pickable=True,
    opacity=0.8,
    stroked=False,
    filled=True,
    extruded=True,
    wireframe=True,
    get_elevation=10
    )


#----------------------------------------------------------------
layers = [
    polygon_layer,
    icon_layer
]

INITIAL_VIEW_STATE = pdk.ViewState(
    latitude=train_stations.loc[station].geometry.y, 
    longitude=train_stations.loc[station].geometry.x,
    zoom=15,
    pitch=45,
    bearing=0
)

map = pdk.Deck(layers,
         map_style='road',
         initial_view_state=INITIAL_VIEW_STATE, 
         tooltip={"text": "WONINGWAARDE 2022: {LABEL}"},
        )

#----------------------------------------------------------------
st.pydeck_chart(map)


#----------------------------------------------------------------


# data_df = df_join.groupby("LABEL",as_index=False).size()
data_df = pd.DataFrame(
    {
        "sales": [200, 550, 1000, 80],
    }
)

st.data_editor(
    data_df,
    column_config={
        "sales": st.column_config.ProgressColumn(
            "Amount",
            help="Number of building for this class",
            format="%f",
            min_value=data_df['size'].min(),
            max_value=data_df['size'].max(),
        ),
    },
    hide_index=True,
)
