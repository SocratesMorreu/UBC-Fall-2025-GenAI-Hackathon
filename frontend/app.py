"""
CampusFlow - Main Streamlit Application
Interactive campus map with issue reporting and AI-powered insights
"""
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import streamlit_folium as st_folium

from map_utils import create_campus_map, load_buildings, load_accessibility, get_smart_recommendations
from api_client import APIClient

# Page configuration
st.set_page_config(
    page_title="CampusFlow",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'reports' not in st.session_state:
    st.session_state.reports = []
if 'trends' not in st.session_state:
    st.session_state.trends = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'student'  # 'student' or 'admin'
if 'selected_building_for_recommendations' not in st.session_state:
    st.session_state.selected_building_for_recommendations = None

# Initialize API client
api_client = APIClient()

# Custom CSS with animations
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1rem;
        animation: fadeInDown 0.8s ease-out;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .summary-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        animation: fadeIn 0.6s ease-out;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .summary-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    .building-card {
        background: white;
        padding: 1rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        animation: slideInRight 0.5s ease-out;
        transition: all 0.3s ease;
        border-left: 4px solid;
        color: #111827 !important;
    }
    
    .building-card strong {
        color: #111827 !important;
    }
    
    .building-card small {
        color: #6b7280 !important;
    }
    
    .building-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    .status-quiet { border-left-color: #3b82f6; }
    .status-busy { border-left-color: #f59e0b; }
    .status-broken { border-left-color: #ef4444; }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        margin: 0.5rem 0;
        animation: fadeIn 0.6s ease-out;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .trend-up {
        color: #10b981;
        animation: pulse 2s infinite;
    }
    
    .trend-down {
        color: #ef4444;
    }
    
    .trend-stable {
        color: #6b7280;
    }
    
    .search-box {
        padding: 0.75rem;
        border-radius: 0.5rem;
        border: 2px solid #e5e7eb;
        transition: border-color 0.3s ease;
    }
    
    .search-box:focus {
        border-color: #667eea;
        outline: none;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    .badge-quiet { background: #dbeafe; color: #1e40af; }
    .badge-busy { background: #fef3c7; color: #92400e; }
    .badge-broken { background: #fee2e2; color: #991b1b; }
    
    .loading-spinner {
        border: 3px solid #f3f4f6;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🏛️ CampusFlow</h1>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; margin-bottom: 2rem; animation: fadeIn 0.8s ease-out;"><h3>Safe, Visual, Data-Driven Campus Management</h3></div>', unsafe_allow_html=True)
    
    # Load buildings data
    buildings = load_buildings()
    building_names = {b['id']: b['name'] for b in buildings}
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Role-based view toggle
        st.subheader("👤 View Mode")
        user_role = st.radio(
            "Select your role:",
            options=["👩‍🎓 Student View", "🧰 Admin View"],
            index=0 if st.session_state.user_role == 'student' else 1,
            key="role_selector"
        )
        st.session_state.user_role = 'student' if "Student" in user_role else 'admin'
        
        st.divider()
        
        # Search functionality
        st.subheader("🔍 Search")
        search_query = st.text_input(
            "Search buildings...",
            placeholder="Type building name...",
            key="search_input"
        )
        
        # Map options
        st.subheader("🗺️ Map Options")
        show_accessibility = st.checkbox("View Accessibility", value=False)
        show_heatmap = st.checkbox("Show Occupancy Heatmap", value=False)
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        
        st.divider()
        
        # Status filter
        st.subheader("📊 Filters")
        status_filter = st.multiselect(
            "Filter by Status",
            options=["quiet", "busy", "broken"],
            default=["quiet", "busy", "broken"]
        )
        
        # Occupancy filter
        occupancy_range = st.slider(
            "Occupancy Range (%)",
            min_value=0,
            max_value=100,
            value=(0, 100),
            step=5
        )
        
        # Building filter
        building_options = ["All"] + list(building_names.values())
        if search_query:
            building_options = ["All"] + [name for name in building_names.values() 
                                         if search_query.lower() in name.lower()]
        
        selected_building = st.selectbox(
            "Filter by Building",
            options=building_options
        )
        
        st.divider()
        
        # Action buttons
        st.subheader("⚡ Actions")
        col1, col2 = st.columns(2)
        with col1:
            show_trends = st.button("📈 Trends", type="primary", use_container_width=True)
        with col2:
            report_issue = st.button("📝 Report", use_container_width=True)
        
        st.divider()
        
        # Status legend
        st.markdown("### 📋 Status Legend")
        st.markdown("🔵 **Blue** = Quiet")
        st.markdown("🟠 **Orange** = Busy")
        st.markdown("🔴 **Red** = Broken/Issues")
        
        # Real-time stats
        st.divider()
        st.markdown("### 📊 Quick Stats")
        total_buildings = len(buildings)
        busy_count = sum(1 for b in buildings if b['status'] == 'busy')
        quiet_count = sum(1 for b in buildings if b['status'] == 'quiet')
        total_occupancy = sum(b.get('occupancy', 0) for b in buildings)
        total_capacity = sum(b.get('capacity', 0) for b in buildings)
        avg_occupancy = (total_occupancy / total_capacity * 100) if total_capacity > 0 else 0
        
        st.metric("Total Buildings", total_buildings)
        st.metric("Average Occupancy", f"{avg_occupancy:.1f}%")
        st.metric("Busy Buildings", busy_count)
        st.metric("Quiet Buildings", quiet_count)
    
    # Filter buildings based on selections
    filtered_buildings = buildings.copy()
    
    # Apply status filter
    if status_filter:
        filtered_buildings = [b for b in filtered_buildings if b['status'] in status_filter]
    
    # Apply occupancy filter
    filtered_buildings = [
        b for b in filtered_buildings
        if occupancy_range[0] <= (b.get('occupancy', 0) / b.get('capacity', 100) * 100) <= occupancy_range[1]
    ]
    
    # Apply building filter
    if selected_building != "All":
        building_id = next((b['id'] for b in buildings if b['name'] == selected_building), None)
        if building_id:
            filtered_buildings = [b for b in filtered_buildings if b['id'] == building_id]
    
    # Apply search filter
    if search_query:
        filtered_buildings = [
            b for b in filtered_buildings
            if search_query.lower() in b['name'].lower()
        ]
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🗺️ Campus Map")
        
        # Show filter info
        if len(filtered_buildings) != len(buildings):
            st.info(f"Showing {len(filtered_buildings)} of {len(buildings)} buildings")
        
        # Create and display map
        campus_map = create_campus_map(
            show_accessibility=show_accessibility,
            show_heatmap=show_heatmap,
            buildings=filtered_buildings
        )
        map_data = st_folium.st_folium(campus_map, width=700, height=600)
        
        # Handle map interactions
        if map_data.get('last_object_clicked_popup'):
            clicked_building = map_data['last_object_clicked_popup']
            st.success(f"📍 Selected: {clicked_building}")
        
        # Auto-refresh functionality (using placeholder for now)
        if auto_refresh:
            st.info("🔄 Auto-refresh enabled - page will refresh every 30 seconds")
            # Note: In production, use st.rerun() with a timer or implement server-side refresh
        
        # Smart Recommendations Section (Student View)
        if st.session_state.user_role == 'student':
            st.divider()
            st.subheader("💡 Smart Recommendations")
            
            # Building selector for recommendations
            recommendation_building = st.selectbox(
                "I'm currently at:",
                options=["Select a building..."] + list(building_names.values()),
                key="recommendation_building_selector"
            )
            
            if recommendation_building and recommendation_building != "Select a building...":
                building_id = next((b['id'] for b in buildings if b['name'] == recommendation_building), None)
                if building_id:
                    current_building = next((b for b in buildings if b['id'] == building_id), None)
                    if current_building:
                        occupancy_pct = (current_building.get('occupancy', 0) / current_building.get('capacity', 100) * 100) if current_building.get('capacity', 100) > 0 else 0
                        
                        # Show recommendations if building is busy
                        if occupancy_pct >= 50 or current_building.get('status') == 'busy':
                            recommendations = get_smart_recommendations(building_id, buildings, max_recommendations=3)
                            
                            if recommendations:
                                st.info(f"**{current_building['name']}** is {current_building['status']} ({occupancy_pct:.0f}% full). Here are some quiet alternatives:")
                                
                                for i, rec in enumerate(recommendations, 1):
                                    rec_building = rec['building']
                                    with st.container():
                                        rec_html = f"""
                                        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                                                    padding: 1rem; border-radius: 0.75rem; margin: 0.5rem 0;
                                                    border-left: 4px solid #3b82f6; animation: slideInRight 0.5s ease-out;">
                                            <strong style="color: #1e40af;">{i}. {rec_building['name']}</strong>
                                            <div style="margin-top: 0.5rem; color: #475569;">
                                                📍 {rec['distance_km']} km away • 🚶 {rec['walk_time_minutes']} min walk
                                            </div>
                                            <div style="color: #64748b; font-size: 0.9em;">
                                                {rec['occupancy_pct']}% occupied • {rec_building.get('status', 'quiet').title()}
                                            </div>
                                        </div>
                                        """
                                        st.markdown(rec_html, unsafe_allow_html=True)
                            else:
                                st.info("No quiet alternatives found nearby. All buildings are busy!")
                        else:
                            st.success(f"✅ **{current_building['name']}** is quiet ({occupancy_pct:.0f}% full). Great spot to study!")
    
    with col2:
        # Role-based content
        if st.session_state.user_role == 'admin':
            st.header("🧰 Admin Dashboard")
            
            # Admin-specific metrics
            col_metric1, col_metric2 = st.columns(2)
            with col_metric1:
                total_reports = len(st.session_state.reports) if st.session_state.reports else 0
                st.metric("Total Reports", total_reports)
            with col_metric2:
                busy_buildings = sum(1 for b in buildings if b['status'] == 'busy')
                st.metric("Busy Buildings", busy_buildings)
            
            st.divider()
        
        st.header("📊 Summary")
        
        # Load and display trends (both views, but more prominent in admin)
        if st.session_state.user_role == 'admin' or show_trends or st.session_state.trends:
            if not st.session_state.trends:
                with st.spinner("Fetching trends..."):
                    st.session_state.trends = api_client.get_trends()
            
            trends = st.session_state.trends
            st.markdown('<div class="summary-box">', unsafe_allow_html=True)
            st.subheader("📈 Today's Trends")
            st.write(trends.get('summary', 'No trends available'))
            
            if trends.get('top_issues'):
                st.subheader("🔝 Top 3 Issues")
                for i, issue in enumerate(trends['top_issues'][:3], 1):
                    building_name = building_names.get(issue['building'], issue['building'])
                    st.markdown(f"**{i}.** {building_name}")
                    st.markdown(f"   *{issue['issue_type']}* ({issue['count']} reports)")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("💡 Click '📈 Trends' to see AI-generated insights")
        
        # Building status summary with enhanced visuals
        st.subheader("🏛️ Building Status")
        
        # Sort by occupancy percentage
        sorted_buildings = sorted(
            filtered_buildings,
            key=lambda x: x.get('occupancy', 0) / x.get('capacity', 100) if x.get('capacity', 100) > 0 else 0,
            reverse=True
        )
        
        for building in sorted_buildings[:10]:  # Show top 10
            status = building.get('status', 'quiet')
            status_emoji = {"quiet": "🔵", "busy": "🟠", "broken": "🔴"}.get(status, "⚪")
            occupancy_pct = (building.get('occupancy', 0) / building.get('capacity', 100) * 100) if building.get('capacity', 100) > 0 else 0
            
            # Create building card HTML with dark text colors
            status_class = f"status-{status}"
            building_html = f"""
            <div class="building-card {status_class}" style="color: #111827;">
                <strong style="color: #111827; font-size: 1rem;">{status_emoji} {building['name']}</strong>
                <div style="margin-top: 0.5rem; color: #6b7280;">
                    <small style="color: #6b7280;">{status.title()} • {building.get('occupancy', 0)}/{building.get('capacity', 0)} ({occupancy_pct:.0f}%)</small>
                </div>
            </div>
            """
            st.markdown(building_html, unsafe_allow_html=True)
            
            # Progress bar with color coding
            progress_value = building.get('occupancy', 0) / building.get('capacity', 100) if building.get('capacity', 100) > 0 else 0
            if occupancy_pct >= 80:
                st.progress(progress_value)
            elif occupancy_pct >= 50:
                st.progress(progress_value)
            else:
                st.progress(progress_value)
    
    # Report Issue Modal
    if report_issue:
        st.session_state.show_report_form = True
    
    if st.session_state.get('show_report_form', False):
        with st.expander("📝 Report an Issue", expanded=True):
            with st.form("issue_report_form"):
                building_options = {b['name']: b['id'] for b in buildings}
                building_name = st.selectbox(
                    "Building",
                    options=list(building_options.keys())
                )
                building_id_selected = building_options[building_name]
                
                issue_type = st.selectbox(
                    "Issue Type",
                    options=["outlet", "accessibility", "crowd", "temperature", "other"]
                )
                
                description = st.text_area(
                    "Description",
                    placeholder="Describe the issue in detail..."
                )
                
                severity = st.select_slider(
                    "Severity",
                    options=["low", "medium", "high"],
                    value="medium"
                )
                
                # Photo upload (S3)
                st.markdown("**📷 Attach Photo (Optional)**")
                uploaded_file = st.file_uploader(
                    "Upload a photo of the issue",
                    type=['png', 'jpg', 'jpeg'],
                    help="Upload an image to help us understand the issue better"
                )
                
                submitted = st.form_submit_button("Submit Report", type="primary")
                
                if submitted:
                    if description.strip():
                        # Upload photo to S3 if provided
                        photo_url = None
                        if uploaded_file is not None:
                            # Display preview
                            st.image(uploaded_file, caption="Photo Preview", width=200)
                            photo_url = api_client.upload_photo(uploaded_file, building_id_selected)
                            if photo_url:
                                st.info("📸 Photo uploaded successfully!")
                        
                        # Submit report
                        response = api_client.submit_report(
                            building=building_id_selected,
                            issue_type=issue_type,
                            description=description,
                            severity=severity,
                            photo_url=photo_url
                        )
                        
                        if response.get('statusCode') == 200 or 'message' in response:
                            st.success("✅ Report submitted successfully!")
                            st.session_state.show_report_form = False
                            st.session_state.trends = None  # Reset trends to refresh
                            st.rerun()
                        else:
                            st.error(f"❌ Error submitting report: {response.get('error', 'Unknown error')}")
                    else:
                        st.warning("Please provide a description of the issue.")
    
    # Accessibility information panel
    if show_accessibility:
        st.header("♿ Accessibility Information")
        accessibility_data = load_accessibility()
        
        for acc in accessibility_data:
            building_name = building_names.get(acc['building_id'], acc['building_id'])
            with st.expander(f"🏛️ {building_name}"):
                st.write(f"**Elevators:** {acc['elevators']}")
                st.write(f"**Accessible Washrooms:** {acc['accessible_washrooms']}")
                st.write(f"**Notes:** {acc['notes']}")
                
                st.subheader("Wheelchair Entrances")
                for entrance in acc['wheelchair_entrances']:
                    st.write(f"📍 {entrance['description']}")

if __name__ == "__main__":
    main()

