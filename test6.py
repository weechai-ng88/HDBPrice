import pandas as pd
import joblib
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import streamlit as st

# Load the data
df = pd.read_csv('ONE.csv')

# Calculate building age
df['building_age'] = 2024 - df['lease_commence_date']
df = df.round(2)

# Set page configuration
st.set_page_config(page_title="HDB Resale Price Prediction", layout="wide")

# Custom CSS to set smaller font size for the page title
st.markdown(
    """
    <style>
    .title-font {
        font-size: 20px;  /* Adjust this value to change the font size */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
    <style>
        .stApp {
            background-color: #eae6d6;  /* Set default background color */
        }
       
        .stTextInput > div > div > input {
            background-color: #FFFFFF;
            color: #000000;
            width: 100%;
        }
        .stHeader {
            color: #333333;
            font-size: 1.5em;  /* Adjust this value to change the font size */
            font-weight: bold;
            margin-bottom: 20px;
        }
        .stLogo {
            width: 200px;  /* Smaller logo size */
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Load the trained XGBoost model
model = joblib.load('xgb_regressor_model.pkl')

# Create two columns with a custom width ratio
left_column, right_column = st.columns([1, 3])

with left_column:
    st.markdown("<div class='left-column'>", unsafe_allow_html=True)

    # Use the correct direct link for your logo image
    logo_url = "https://i.imgur.com/gZ4Pg1m.png"  # This is the direct link to your image
   
    # Display the logo centered
    st.markdown(f"<img src='{logo_url}' class='stLogo'>", unsafe_allow_html=True)
    
    # Display the header text centered below the logo
    st.markdown("<div class='stHeader'>HDB Resale Price Prediction</div>", unsafe_allow_html=True)
                
# Check if 'postal' column exists
if 'postal' not in df.columns:
    left_column.write("Error: postal code not found. Please enter a HDB flat that is primed for resale.")
else:
    # Create a dictionary mapping postal codes to relevant data
    precomputed_data = df.set_index('postal').T.to_dict()

    @st.cache_data
    def get_data_by_postal_code(postal_code):
        return precomputed_data.get(postal_code, None)

    # Streamlit UI in the left column
    postal_code = left_column.text_input("Enter Postal Code", max_chars=6)
    
    # Additional inputs for floor level and floor area
    floor_level = left_column.text_input("Enter Floor Level", max_chars=2)
    floor_area_sqm = left_column.text_input("Enter Floor Area (sqm)", max_chars=5)
    
    if postal_code and floor_level and floor_area_sqm:
        data = get_data_by_postal_code(postal_code)
        if data:
            # Collect all relevant data
            data['floor_level'] = int(floor_level)
            data['floor_area_sqm'] = float(floor_area_sqm)
            
            # Set mid_storey directly as the floor_level
            mid_storey = data['floor_level']
            
            # Display the input data
            left_column.write(f"Town name: {data.get('planning_area', 'N/A')}")
            left_column.write(f"MRT Nearest Location: {data.get('mrt_name', 'N/A')} station")
            left_column.write(f"Mall Nearest Distance: {data.get('Mall_Nearest_Distance', 'N/A')} m")
            left_column.write(f"MRT Nearest Distance: {data.get('mrt_nearest_distance', 'N/A')} m")
            left_column.write(f"Nearest Primary School: {data.get('pri_sch_name', 'N/A')}")
            left_column.write(f"Primary School Nearest Distance: {data.get('pri_sch_nearest_distance', 'N/A')} m")
            left_column.write(f"Full Flat Type: {data.get('full_flat_type', 'N/A')}")
            left_column.write(f"Building Age: {data.get('building_age', 'N/A')} years")
            left_column.write(f"Max Floor: {data.get('max_floor_lvl', 'N/A')}")
            left_column.write(f"Floor Level: {floor_level}")
            left_column.write(f"Floor Area: {floor_area_sqm} sqm")
            
            # Prepare the data for prediction
            input_data = pd.DataFrame({
                'fft_Encoded': [data.get('fft_Encoded', 0)],
                'MRT_encoded': [data.get('MRT_encoded', 0)],
                'building_age': [data.get('building_age', 0)],
                'Tranc_Year': [2024],  # Use the current year or extract it dynamically
                'Tranc_Month': [8],    # Use the current month or extract it dynamically
                'floor_area_sqm': [float(floor_area_sqm)],  # Ensure this is a float
                'max_floor_lvl': [data.get('max_floor_lvl', 0)],
                'mid_storey': [mid_storey],  # Directly use floor_level as mid_storey
                'pa_Encoded': [data.get('PA_encoded', 0)],
                'Mall_Nearest_Distance': [data.get('Mall_Nearest_Distance', 0)],
                'Hawker_Nearest_Distance': [data.get('Hawker_Nearest_Distance', 0)],
                'mrt_nearest_distance': [data.get('mrt_nearest_distance', 0)],
                'pri_sch_nearest_distance': [data.get('pri_sch_nearest_distance', 0)],
                'Pri_School_encoded': [data.get('Pri_School_encoded', 0)]
            })

            # Make the prediction
            predicted_price = model.predict(input_data)
            left_column.write(f"Predicted Resale Price: ${predicted_price[0]:,.2f}")
        else:
            left_column.write("Postal code not found. Please enter a HDB flat that is primed for resale.")

# Function to get coordinates from postal code and focus on Singapore
def get_coordinates(postal_code):
    geolocator = Nominatim(user_agent="streamlit-app")
    
    try:
        # Specify location as Singapore by adding 'SG' to the query
        location = geolocator.geocode(f"{postal_code}, Singapore")
        
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except GeocoderTimedOut:
        return None  # Handle the case where the geocoding times out

# Context about HDB resale price in the right column
with right_column:
    right_column.subheader("Optimising Resale Price Strategy for Singapore HDBs")
    right_column.write("""
    This tool gives WOW housing agents accurate, data-driven HDB resale price estimates. By entering details like postal code, floor level, and area, agents can assess pricing trends and make informed recommendations based on market data and conditions.
    """)
    
    # Initialize the map centered on Singapore
    singapore_coordinates = (1.3521, 103.8198)  # Singapore's latitude and longitude
    map_object = folium.Map(location=singapore_coordinates, zoom_start=12)  # Adjust the zoom_start value to control the zoom level

    # If postal code is provided, update the map with the specific location
    if postal_code:
        coordinates = get_coordinates(postal_code)
        
        if coordinates:
            # Update the map location and zoom level after retrieving the coordinates
            map_object = folium.Map(location=coordinates, zoom_start=18)  # Set zoom to 18 for a closer view
            
            # Add a marker at the location with an improved popup
            marker = folium.Marker(location=coordinates, popup=f"Location: {postal_code}")
            marker.add_to(map_object)
        else:
            right_column.error("Postal code not found or invalid. If you've entered a postal code starting with a zero, such as 085055. Please remove the leading zero and enter a valid HDB flat postal code for resale, like 85055 instead.")

    # Display the map in Streamlit
    st_folium(map_object, width=1000, height=600)
