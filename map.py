import streamlit as st, folium, geopandas as gpd,pandas as pd
from folium import plugins
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import base64
geo_data_path = '../data/manual/geo_data1.shp'
rbc_data_path = '../data/manual/rbc.shp'
hf_location_path = '../data/manual/hf_location.xlsx'
st.cache_data.clear()
@st.cache_data()
# def get_base64_of_bin_file(bin_file):
#     with open(bin_file, 'rb') as f:
#         data = f.read()
#     return base64.b64encode(data).decode()

# def set_png_as_page_bg(png_file):
#     bin_str = get_base64_of_bin_file(png_file)
#     page_bg_img = '''
#     <style>
#     body {
#     background-image: url("data:image/png;base64,%s");
#     background-size: cover;
#     }
#     </style>
#     ''' % bin_str
    
#     st.markdown(page_bg_img, unsafe_allow_html=True)
#     return

#set_png_as_page_bg('background.png')
def load_data():
    df = gpd.read_file(geo_data_path).rename(columns={
        'NOMBER OF': 'NOMBER OF CASES',
        'Total': 'Population',
        'Disease_Pr': 'Disease Prevalence(%)'
    })
    rbc_data = gpd.read_file(rbc_data_path)
    location_data = pd.read_excel(hf_location_path)
    return df, rbc_data, location_data.dropna()

def get_marker_color(hftype):
    color_mapping = {
        "HEALTH POST": 'gray',
        "HEALTH CENTER": 'orange',
        "PHARMACY": 'purple',
        "REFERENCE HOSPITAL": 'pink',
        "HOSPITAL": 'blue',
        "PROVINCIAL HOSPITAL": 'lightblue',
        "Private Hospital": 'darkblue',
        "Medical Clinic": 'red',
        "DENTAL CLINIC": 'darkred',
        "POLYCLINIC": 'darkpurple',
        "CLINIC": 'lightred',
        "BUSINESS": 'lightgray',
        "LABORATORY": 'green',
        "GOVERNMENT INSTITUTION": 'lightgreen',
        "DISPENSARY": 'darkgreen',
        "SUPPLIER": 'cadetblue',
        "UNIVERSITY": 'beige',
        "NGO": 'white',
        "CHURCH": 'black'
    }
    return color_mapping.get(hftype, '#4df3ce')

def add_marker(facility_row,map):
    facility_type = facility_row['FACILITY TYPE']
    #folium.CircleMarker(
    folium.Marker(
        location=[facility_row["Latitude"], facility_row["Longitude"]],
        #radius=3,
        #color=get_marker_color(facility_type),
        #fill=True,
        #fill_color=get_marker_color(facility_type),
        #fill_opacity=0.7,
        popup = folium.Popup(f"HEALTH FACILITY:{facility_row['HEALTH FACILITY']}\nFACILITY TYPE: {facility_row['FACILITY TYPE']}\nProvince: {facility_row['Province']}\n District: {facility_row['District']}     \n Sector: {facility_row['Sector']}", max_width=150, parse_html=True),#Cell: {facility_row['Cell']}, Village: {facility_row['Village']}
        tooltip=folium.Tooltip(f"HEALTH FACILITY: {facility_row['HEALTH FACILITY']}, FACILITY TYPE: {facility_row['FACILITY TYPE']}"),
        icon=folium.Icon(color=get_marker_color(facility_type))
    ).add_to(map)

def display_crosstab_table():
    crosstab_table = pd.crosstab(
        [location_data['HEALTH FACILITY'], location_data['FACILITY TYPE'], location_data['Province'], location_data['District'], location_data['Sector'], location_data['FACILITY TYPE']],
        location_data['FACILITY TYPE'],
        values=location_data['FACILITY TYPE'],
        aggfunc=pd.Series.unique
    )
    st.dataframe(crosstab_table)

def main():
    df, rbc_data, location_data = load_data()
    st.title("Mapping Healthcare Services in Rwanda")
    # Create a dropdown menu to select the disease
    selected_disease = st.sidebar.selectbox('Select a Disease', df['DISEASES'].unique())
    selected_hf = st.sidebar.multiselect('Select a Facility', location_data['HEALTH FACILITY'].unique().tolist())
    selected_hf_typ = st.sidebar.multiselect('Select a Facility Type',location_data['FACILITY TYPE'].unique().tolist())
    #st.write(location_data['FACILITY T'].unique())
    selected_equipment = st.sidebar.selectbox('Select an Equipment', [""] + rbc_data['EQUIPMENT'].unique().tolist())  
    # Iterate through data and add markers to the map
    # Create a map
    map = folium.Map(location=[-1.93, 29.9], zoom_start=9, control_scale=True)
    plugins.Fullscreen(position='topright').add_to(map)
    #for index, facility_row in location_data.iterrows():
        #add_marker(facility_row, map)
    filtered_data = location_data.copy()
    if selected_hf:
        filtered_data = filtered_data[filtered_data['HEALTH FACILITY'].isin(selected_hf)]
    if selected_hf_typ:
        filtered_data = filtered_data[filtered_data['FACILITY TYPE'].isin(selected_hf_typ)]
    if selected_hf_typ and selected_hf:
        filtered_data = filtered_data[(filtered_data['HEALTH FACILITY'].isin(selected_hf))&(filtered_data['FACILITY TYPE'].isin(selected_hf_typ))] 
    if selected_equipment:
        st.error('Sorry this Feature is still Under Implementation', icon="🚨")   
    for index, facility_row in filtered_data.iterrows():
        add_marker(facility_row,map)

    data=df[df['DISEASES'] == selected_disease]
    #metric_title = f'{selected_disease} Prevalence in Rwanda'
    #rwd_per_disease_pr = (((data['NOMBER OF CASES'].sum()) / data['Population'].sum()) * 100).round(2)
    #st.metric(metric_title, rwd_per_disease_pr)
    # Create a GeoJson layer for the sectors
    sectors_layer = folium.FeatureGroup(name='Sectors')
    folium.GeoJson(
    data,
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
    choropleth = folium.Choropleth(
        geo_data=data,
        data=data,
        columns=['Sector', 'Disease Prevalence(%)'],
        key_on='feature.properties.Sector',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        highlight=True,
        highlight_function=lambda x: {"fillOpacity": 0.8},
        zoom_on_click=True,
        legend_name=f'{selected_disease} Prevalence (%)'
    )

    # Create a GeoJsonTooltip for the choropleth
    #marker=folium.Circle(radius=4, fill_color="orange", fill_opacity=0.4, color="black", weight=1)
    popup=folium.GeoJsonPopup(fields=["Province", "District", "Sector"])
    tooltip = folium.GeoJsonTooltip(
        fields=['Province', 'District', 'Sector','NOMBER OF CASES',
       'Population', 'Male', 'Female'],
        aliases=['Province', 'District', 'Sector','NOMBER OF CASES',
       'Population', 'Male', 'Female'],
        localize=True
    )
    choropleth.geojson.add_child(tooltip)
    choropleth.geojson.add_child(popup)
    choropleth.add_to(map)
    folium_static(map,width=775,height=650)

if __name__ == "__main__":
    main()
