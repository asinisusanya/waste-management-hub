import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
from scipy.optimize import minimize
import folium
from streamlit_folium import st_folium
import warnings

warnings.filterwarnings('ignore')

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="Waste Processing Zone Optimizer",
    page_icon="♻️",
    layout="wide",
)

# ------------------------------------------------
# HEADER
# ------------------------------------------------
st.markdown("""
<div style="text-align:center; padding: 10px;">
    <h1 style="color:#007B83;">♻️ OPTIMIZATION MODEL FOR WASTE PROCESSING ZONE LOCATION IN BOI ZONES</h1>
    <p style="font-size:17px; color:#333;">
    This application identifies the <b>optimal location</b> for a centralized Waste Processing Zone among Sri Lanka’s BOI zones.  
    It minimizes total transportation costs while considering exclusion zones and sensitive sites.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ------------------------------------------------
# LOAD GEOGRAPHIC DATA
# ------------------------------------------------
@st.cache_resource
def load_geographic_data():
    world = gpd.read_file("data/SLBdd/ne_110m_admin_0_countries.shp")
    sri_lanka = world[world['NAME'] == 'Sri Lanka']
    sri_lanka_polygon = sri_lanka.geometry.unary_union

    protected_areas_1 = gpd.read_file("data/Protected/WDPA_WDOECM_Aug2025_Public_LKA_shp-points.shp")
    protected_areas_2 = gpd.read_file("data/Other/Water_Bodies_and_Rivers.geojson")
    buffer_zones = gpd.read_file("data/Other/Sensitive_Sites_Schools_Hospitals_Religious Places_Parks.geojson")

    crs = sri_lanka.crs
    exclusion_layers = [protected_areas_1, protected_areas_2, buffer_zones]
    for gdf in exclusion_layers:
        if gdf.crs != crs:
            gdf.to_crs(crs, inplace=True)

    all_exclusion = gpd.GeoDataFrame(pd.concat(exclusion_layers, ignore_index=True), crs=crs)
    all_exclusion_union = unary_union(all_exclusion.geometry)
    exclusion_clipped = all_exclusion_union.intersection(sri_lanka_polygon)

    sensitive_points = buffer_zones.copy()
    sensitive_coords = [(geom.x, geom.y) for geom in sensitive_points.geometry]
    buffer_distance = 0.0001

    return sri_lanka_polygon, exclusion_clipped, sensitive_coords, buffer_distance


try:
    sri_lanka_polygon, exclusion_clipped, sensitive_coords, buffer_distance = load_geographic_data()
except Exception as e:
    st.error(f"⚠️ Required geographic files not found.\n\n{e}")
    st.stop()

# ------------------------------------------------
# LAYOUT — INPUT LEFT / OUTPUT RIGHT
# ------------------------------------------------
left_col, right_col = st.columns([0.8, 2.2])  # narrower input panel

with left_col:
    st.markdown("<h3 style='color:#007B83;'>🗺️ Input Zone Details</h3>", unsafe_allow_html=True)
    n = st.number_input("Number of BOI Zones", min_value=1, max_value=20, value=5, step=1)

    zone_data = []
    for i in range(int(n)):
        with st.expander(f"Zone {i+1} Details", expanded=(i == 0)):
            name = st.text_input(f"Name", value=f"Zone {i+1}", key=f"name_{i}")
            lon = st.number_input("Longitude", value=80.0 + i * 0.1, key=f"lon_{i}", format="%.6f")
            lat = st.number_input("Latitude", value=6.9 + i * 0.05, key=f"lat_{i}", format="%.6f")
            waste = st.number_input("Waste Quantity (tons/day)", min_value=0.0, value=2000.0, key=f"waste_{i}")
            zone_data.append({"Zone Name": name, "Longitude": lon, "Latitude": lat, "Waste Quantity": waste})

    st.markdown("<br>", unsafe_allow_html=True)
    run_opt = st.button("🚀 Run Optimization", use_container_width=True)

# ------------------------------------------------
# OPTIMIZATION LOGIC
# ------------------------------------------------
if run_opt and zone_data:
    # Clear previous outputs
    st.session_state.pop("result", None)
    st.session_state.pop("map", None)

    df = pd.DataFrame(zone_data)

    # --- Helper functions ---
    def inside_sri_lanka(x, y):
        return sri_lanka_polygon.contains(Point(x, y))

    def outside_exclusion(x, y):
        return not exclusion_clipped.contains(Point(x, y))

    def respect_buffer(x, y):
        for (xf, yf) in sensitive_coords:
            if np.sqrt((x - xf)**2 + (y - yf)**2) < buffer_distance:
                return False
        return True

    def is_feasible(xy):
        x, y = xy
        return inside_sri_lanka(x, y) and outside_exclusion(x, y) and respect_buffer(x, y)

    # --- Objective Function ---
    vehicle_capacity = 5 / 1000
    cost_per_km = 20 / 1000
    df['Q'] = df['Waste Quantity'] / 1000

    def objective(xy):
        x, y = xy
        if not is_feasible(xy):
            return 1e9
        total_cost = 0
        for _, row in df.iterrows():
            xi, yi, Qi = row['Longitude'], row['Latitude'], row['Q']
            ni = np.ceil(Qi / vehicle_capacity)
            ti = np.sqrt((xi - x)**2 + (yi - y)**2)
            total_cost += cost_per_km * ni * ti
        return total_cost

    # Optimization
    x0 = [df['Longitude'].mean(), df['Latitude'].mean()]
    bounds = [(df['Longitude'].min(), df['Longitude'].max()),
              (df['Latitude'].min(), df['Latitude'].max())]
    result = minimize(objective, x0, method="L-BFGS-B", bounds=bounds)

    if result.success:
        opt_x, opt_y = result.x
        st.session_state["result"] = {"x": opt_x, "y": opt_y, "zones": df}
        st.success("✅ Optimization complete! Check the map on the right.")
    else:
        st.error("Optimization failed. Please check your inputs or constraints.")

# ------------------------------------------------
# OUTPUT SECTION — RIGHT SIDE
# ------------------------------------------------
with right_col:
    st.markdown("<h3 style='color:#007B83;'>📈 Optimization Results</h3>", unsafe_allow_html=True)

    if "result" in st.session_state:
        res = st.session_state["result"]
        opt_x, opt_y, df = res["x"], res["y"], res["zones"]

        st.markdown(
            f"""
            <div style='background-color:#e8f8f6; padding:15px; border-radius:10px; text-align:center;'>
                <h4 style='color:#007B83;'>Optimal Waste Processing Zone</h4>
                <p style='font-size:16px; color:#333;'>
                <b>Longitude:</b> {opt_x:.6f} | <b>Latitude:</b> {opt_y:.6f}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Create static map if not cached
        if "map" not in st.session_state:
            avg_lat, avg_lon = df["Latitude"].mean(), df["Longitude"].mean()
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7, control_scale=True)

            # Add BOI zones
            for _, row in df.iterrows():
                folium.Marker(
                    location=[row["Latitude"], row["Longitude"]],
                    popup=f"{row['Zone Name']}<br>Waste: {row['Waste Quantity']} tons/day",
                    icon=folium.Icon(color="blue", icon="industry", prefix="fa")
                ).add_to(m)

            # Add optimal hub
            folium.Marker(
                location=[opt_y, opt_x],
                popup="Optimal Waste Processing Hub",
                icon=folium.Icon(color="red", icon="star", prefix="fa")
            ).add_to(m)

            st.session_state["map"] = m

        # Center-aligned map display
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st_folium(st.session_state["map"], width=950, height=550)
        st.markdown("</div>", unsafe_allow_html=True)
