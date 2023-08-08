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

st.markdown("""
<style>
.reportview-container .main .block-container {
    max-width: 50%;
    
}
.sidebar .sidebar-content {
    width: 300px;
    background-color: #F5F5F5;
    color: #000000;
    font-size: 10px;
}
</style>
""", unsafe_allow_html=True)


left, right = st.columns([2,3])
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

BUFFER = st.sidebar.slider('Creating buffer from the train stattion (meters)', 0, 1000, 500)
# Creating 1km buffer column with WKT geometry
train_stations['buffer_geom'] = train_stations.buffer(int(BUFFER)) 

# Converting back to original CRS
train_stations.to_crs(crs=4979, inplace=True) 

# Setting the geometry column to the buffer geometry
train_stations.set_geometry("buffer_geom", inplace=True)

# set name as index
train_stations.set_index("name", inplace=True)

#----------------------------------------------------------------
station = st.sidebar.selectbox(label="Chose a station", options=train_stations.index, label_visibility="visible")

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
import altair as alt

source = df_join.groupby("LABEL",as_index=False).size()

domain = df_join.LABEL.sort_values().unique().tolist()
range_ = list(sns.color_palette("husl", len(df_join.LABEL.sort_values().unique())).as_hex())

base = alt.Chart(source).encode(
    y=alt.Y('LABEL:O',title=""),
    x=alt.X('size:Q',title="Number of buildings",axis=None),
    color=alt.Color('LABEL:O',legend=None, scale=alt.Scale(domain=domain, range=range_)),
    text='size:Q'
)

bar = base.mark_bar(
    cornerRadiusBottomRight=3,
    cornerRadiusTopRight=3,
    
)

text = base.mark_text(align='left', dx=2)

st.sidebar.altair_chart(altair_chart=(bar + text), use_container_width=True, theme="streamlit")

if len(source) == 0:
    st.sidebar.warning('If no buildings are showing, try a larger buffer', icon="📏")
