import streamlit as st
import pandas as pd
import geopandas as gpd
import osmnx as ox
import seaborn as sns
import pydeck as pdk



st.set_page_config(
    page_title="Urban_1",
    page_icon=":world_map:️",
    layout="wide",
)

#---
# @st.cache_data
# def data_buildings():
#     df = pd.DataFrame()
#     for i in range(10):
#         gdf = gpd.read_file(f'buildings_{i}.geojson')
#         df = df.append(gdf, ignore_index=True)
#     return df

@st.cache_data
def data():
    buildings = gpd.read_file(f'buildings_0.geojson')
    train_stations = gpd.read_file(f'train_stations.geojson')
    return buildings, train_stations
    
buildings = data()[0]
train_stations = data()[1]

train_stations.plot()

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


#----------------------------------------------------------------

try:
    station = st.selectbox(label="Chose a station", options=train_stations.index, placeholder="Select...", label_visibility="visible")
    
    buildings.to_crs(crs=train_stations.crs, inplace=True) 
    intersected = buildings[buildings['geometry'].intersects(train_stations.loc[station, 'buffer_geom'])]
    
    df_WONINGWAARDE_2022 = gpd.read_file("https://maps.amsterdam.nl/open_geodata/geojson_lnglat.php?KAARTLAAG=WONINGWAARDE_2022&THEMA=woningwaarde")
    st.warning("Some problem")
    df_join = gpd.sjoin(intersected, df_WONINGWAARDE_2022.to_crs(intersected.crs))
    df_join.to_crs(crs=4979, inplace=True) 
    
    
    INITIAL_VIEW_STATE = pdk.ViewState(
        latitude=train_stations.loc[station].geometry.y, 
        longitude=train_stations.loc[station].geometry.x,
        zoom=15,
        pitch=45,
        bearing=0
    )
    
    
    ICON_URL = "https://i2.wp.com/www.banksandlloyd.com/wp-content/uploads/2018/10/train-icon-web-small.png?ssl=1"
    
    data = train_stations.loc[station]
    
    icon_data = {
        "url": ICON_URL,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }
    
    data["icon_data"] = icon_data
    data = data.to_frame().T[["geometry","icon_data"]].reset_index()
    
    
    icon_layer = pdk.Layer(
        type="IconLayer",
        data=data,
        get_icon="icon_data",
        size_scale=60,
        get_position=[train_stations.loc[station].geometry.x, 
                      train_stations.loc[station].geometry.y],
        pickable=True,
    )
    
    
    colors = dict(zip(df_join.LABEL.sort_values().unique().tolist(),list(sns.color_palette("husl", len(df_join.LABEL.sort_values().unique())))))
    
    df_polygons = df_join[["geometry","LABEL"]]
    df_polygons['color'] = df_polygons["LABEL"].map(colors).apply(lambda x: [i*255 for i in x])
    st.warning("Some problem")
    
    layers = [
        pdk.Layer("GeoJsonLayer", 
                  data=df_polygons , 
                  get_fill_color='color',
                  pickable=True,
                  opacity=0.8,
                    stroked=False,
                    filled=True,
                    extruded=True,
                    wireframe=True,
                  get_elevation=10
                 ),
        icon_layer
        
    ]
    
    
    
    map = pdk.Deck(layers,
             map_style='road',
             initial_view_state=INITIAL_VIEW_STATE, 
             tooltip={"text": "{index}, {LABEL}"},
            )
    
    st.pydeck_chart(pydeck_obj=map, use_container_width=True)

except:
    st.warning("Some problem")
