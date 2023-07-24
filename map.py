#https://blog.streamlit.io/scienceio-manages-billions-of-rows-of-training-data-with-streamlit/
import streamlit as st
import folium
import geopandas as gpd
import warnings
warnings.filterwarnings('ignore')
from folium import plugins
from folium.plugins import MeasureControl
from streamlit_folium import folium_static, st_folium
#import git_lfs
#st.cache_data
import subprocess
subprocess.run(['git', 'lfs', 'ls-files', 'geo_data1.shp','geo_data1.cpg','geo_data1.dbf','geo_data1.prj','geo_data1.shx'])
import fiona
from contextlib import contextmanager

# Define a context manager to set the configuration option
@contextmanager
def fiona_env():
    with fiona.Env():
        fiona.env['SHAPE_RESTORE_SHX'] = 'YES'
        yield
# Read the shapefile using GeoPandas within the fiona_env context
with fiona_env():
    shape_file_sectors = gpd.read_file('geo_data1.shp')
#shape_file_sectors = gpd.read_file('geo_data1.shp')
shape_file_sectors=shape_file_sectors.rename(columns={'NOMBER OF':'NOMBER OF CASES','Total':'Population','Disease_Pr':'Disease Prevalence(%)'})
df = shape_file_sectors
def main():
    st.title("Mapping Healthcare Services in Rwanda")
    #st.caption("Visualizing Services Care in Rwanda")

    # Create a dropdown menu to select the disease
    selected_disease = st.sidebar.selectbox('Select a Disease', df['DISEASES'].unique())
    filtered_data = df[df['DISEASES'] == selected_disease]
    # year_list=list(df['Year'].unique())
    # year_list.sort()
    # year=st.sidebar.selectbox('Year',year_list,len(year_list)-1)
    # quater_list=list(df['Quarter'].unique())
    # #quater_list.sort()
    # quater=st.sidebar.selectbox('Quarter',quater_list,len(quater_list)-1)
    # # Filter the data based on the selected disease
    # if year:
    #     filtered_data = df[(df['DISEASES'] == selected_disease)&(df['Year'] == year)]
    # elif quater:
    #     filtered_data = df[(df['DISEASES'] == selected_disease)&(df['Year'] == year)&(df['Quarter'] == quater)]
    # else:
    #     filtered_data = df[df['DISEASES'] == selected_disease]
    metric_title = f'{selected_disease} Prevalence in Rwanda'
    rwd_per_disease_pr = (((filtered_data['NOMBER OF CASES'].sum()) / filtered_data['Population'].sum()) * 100).round(2)
    st.metric(metric_title, rwd_per_disease_pr)

    # Create a map
    map = folium.Map(location=[-1.9437057, 29.8805778], zoom_start=9, control_scale=True)
    plugins.Fullscreen(position='topright').add_to(map)

    # Create a GeoJson layer for the sectors
    sectors_layer = folium.FeatureGroup(name='Sectors')
    folium.GeoJson(
    filtered_data,
    name='Sectors',
    style_function=lambda feature: {
        'color': 'black',
        'fillColor': 'white',
        'weight': 1,
        'fillOpacity': 0.5
    }
    ).add_to(sectors_layer)
    sectors_layer.add_to(map)

    # Create a search control for sector search
    search = plugins.Search(
        layer=sectors_layer,
        geom_type='polygon',
        search_zoom=13,
        placeholder='Search a sector',
        collapsed=False,
        search_label='Sector'
    )

    # Add the Search control to the map
    map.add_child(search)

    # Create a choropleth map for the selected disease
    choropleth = folium.Choropleth(
        geo_data=filtered_data,
        data=filtered_data,
        columns=['Sect_ID', 'Disease Prevalence(%)'],
        key_on='feature.properties.Sect_ID',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        highlight=True,
        legend_name=f'{selected_disease} Prevalence (%)'
    )

    # Create a GeoJsonTooltip for the choropleth
    tooltip = folium.GeoJsonTooltip(
        fields=['Province', 'District', 'Sector','NOMBER OF CASES',
       'Population', 'Male', 'Female'],
        aliases=['Province', 'District', 'Sector','NOMBER OF CASES',
       'Population', 'Male', 'Female'],
        localize=True
    )
    choropleth.geojson.add_child(tooltip)
    choropleth.add_to(map)
    # st_map=st_folium(map,width=600,height=500)
    # if st_map['last_active_drawing']:
    #     st.write(st_map['last_active_drawing']['properties']['DISEASES'])
    # Render the Folium map in Streamlit
    folium_static(map,width=600,height=500)

if __name__ == "__main__":
    main()
