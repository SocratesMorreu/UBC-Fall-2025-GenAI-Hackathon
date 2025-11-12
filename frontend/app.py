"""
CampusFlow - Main Streamlit Application with Voice
"""
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from collections import Counter
import streamlit_folium as st_folium
import os
from dotenv import load_dotenv

load_dotenv()

from map_utils import create_campus_map, load_buildings, load_accessibility, calculate_distance
from api_client import APIClient

try:
    from polly_client import PollyClient
    polly_client = PollyClient()
except ImportError:
    polly_client = None

st.set_page_config(
    page_title="ubica",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path(__file__).parent.parent / "data"

def load_json_data(filename: str, default):
    path = DATA_DIR / filename
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def load_issues_data():
    return load_json_data("issues.json", [])

def load_predictions_data():
    return load_json_data("predictions.json", {})

# Initialize session state
if 'reports' not in st.session_state:
    st.session_state.reports = []
if 'trends' not in st.session_state:
    st.session_state.trends = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'student'
if 'selected_building_for_recommendations' not in st.session_state:
    st.session_state.selected_building_for_recommendations = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_input' not in st.session_state:
    st.session_state.chat_input = ''
if 'voice_counter' not in st.session_state:
    st.session_state.voice_counter = 0

api_client = APIClient()

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">🏛️ ubica</h1>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; margin-bottom: 2rem;"><h3>Safe, Visual, Data-Driven Campus Management with Voice</h3></div>', unsafe_allow_html=True)
    
    buildings = load_buildings()
    building_names = {b['id']: b['name'] for b in buildings}
    building_lookup = {b['id']: b for b in buildings}
    issues = load_issues_data()
    predictions = load_predictions_data()
    
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1.5rem; border-radius: 1rem; margin-bottom: 1.5rem;">
            <h2 style="color: white; margin: 0; text-align: center;">🤖 AI Voice Assistant</h2>
            <p style="color: rgba(255,255,255,0.9); text-align: center; margin-top: 0.5rem;">
                Ask me anything about campus!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Voice settings
        voice_enabled = False
        selected_voice = "Joanna"
        if polly_client and polly_client.available:
            with st.expander("🔊 Voice Settings", expanded=False):
                voice_enabled = st.checkbox("Enable text-to-speech", value=False)
                if voice_enabled:
                    voice_options = ['Joanna', 'Matthew', 'Amy', 'Brian', 'Emma', 'Olivia']
                    selected_voice = st.selectbox("Voice", voice_options)
        
        st.markdown("### 💬 Ask Your Question")
        chat_query = st.text_area(
            "Question",
            placeholder="Need help finding space or reporting an issue?",
            key="chat_input_field",
            height=120,
            label_visibility="collapsed"
        )
        
        col_ask, col_clear = st.columns([2, 1])
        with col_ask:
            ask_button = st.button("🚀 Ask AI", type="primary", use_container_width=True)
        with col_clear:
            if st.button("🗑️", use_container_width=True, help="Clear chat history"):
                st.session_state.chat_history = []
                st.rerun()
        
        if ask_button and chat_query.strip():
            with st.spinner("🤔 Thinking..."):
                response = api_client.chat(chat_query)
                st.session_state.chat_history.append({
                    "query": chat_query,
                    "response": response,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                st.session_state.voice_counter += 1
                st.rerun()
        
        # Display chat history
        if st.session_state.chat_history:
            st.markdown("---")
            st.markdown("### 💬 Conversation History")
            
            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
                with st.container():
                    # User message
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.5rem;
                                color: white;">
                        <div style="font-size: 0.7em; opacity: 0.9;">{chat['timestamp']} • You</div>
                        <div style="font-weight: 500;">{chat['query']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # AI response
                    st.markdown(f"""
                    <div style="background: white; padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.5rem;
                                border-left: 3px solid #667eea; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-size: 0.7em; color: #6b7280;">🤖 AI Assistant</div>
                        <div style="color: #1f2937; line-height: 1.6;">{chat['response']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Voice button
                    if voice_enabled and polly_client and polly_client.available:
                        if st.button(f"🔊 Play Voice", key=f"voice_{st.session_state.voice_counter}_{i}"):
                            audio_bytes = polly_client.synthesize_speech(chat['response'], selected_voice)
                            if audio_bytes:
                                import base64
                                audio_b64 = base64.b64encode(audio_bytes).decode()
                                audio_html = f"""
                                <audio controls autoplay style="width: 100%; margin: 10px 0;">
                                    <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                                </audio>
                                """
                                st.markdown(audio_html, unsafe_allow_html=True)
                                st.success("🔊 Audio ready!")
                    
                    st.divider()
        
        report_issue = st.button("📝 Report an Issue", use_container_width=True)
        
        st.divider()
        
        st.markdown("### 🗺️ Map Options")
        show_accessibility = st.checkbox("View Accessibility", value=False)
        show_heatmap = st.checkbox("Show Occupancy Heatmap", value=False)
        
        st.divider()

        st.markdown("### 🧭 Wayfinder")
        building_list = ["Select a building..."] + list(building_names.values())
        start_building_name = st.selectbox("From", building_list, key="wayfinder_start")
        end_building_name = st.selectbox("To", building_list, key="wayfinder_end")
        
        st.divider()
        
        st.markdown("### 👤 View Mode")
        user_role = st.radio(
            "Select your role:",
            options=["👩🎓 Student View", "🧰 Admin View"],
            index=0 if st.session_state.user_role == 'student' else 1,
            key="role_selector",
            label_visibility="collapsed"
        )
        st.session_state.user_role = 'student' if "Student" in user_role else 'admin'
        
        st.divider()
        
        st.markdown("### 📊 Quick Stats")
        total_buildings = len(buildings)
        busy_count = sum(1 for b in buildings if b['status'] == 'busy')
        quiet_count = sum(1 for b in buildings if b['status'] == 'quiet')
        
        st.metric("Total Buildings", total_buildings)
        st.metric("Busy Buildings", busy_count)
        st.metric("Quiet Buildings", quiet_count)
    
    # Main content
    st.header("🗺️ Campus Map")

    # Wayfinder route
    route_points = None
    route_details = None
    if (
        start_building_name
        and end_building_name
        and start_building_name != "Select a building..."
        and end_building_name != "Select a building..."
        and start_building_name != end_building_name
    ):
        start_building = next((b for b in buildings if b['name'] == start_building_name), None)
        end_building = next((b for b in buildings if b['name'] == end_building_name), None)
        if start_building and end_building:
            route_points = [
                (start_building['lat'], start_building['lon']),
                (end_building['lat'], end_building['lon'])
            ]
            distance_km = calculate_distance(
                start_building['lat'], start_building['lon'],
                end_building['lat'], end_building['lon']
            )
            walk_time_minutes = int((distance_km / 5) * 60) if distance_km > 0 else 0
            route_details = {
                "from": start_building_name,
                "to": end_building_name,
                "distance_km": distance_km,
                "walk_time_minutes": walk_time_minutes
            }

    # Create and display map
    campus_map = create_campus_map(
        show_accessibility=show_accessibility,
        show_heatmap=show_heatmap,
        buildings=buildings,
        wayfinder_route=route_points
    )
    map_data = st_folium.st_folium(campus_map, width=900, height=600)

    # Handle map interactions
    if map_data.get('last_object_clicked_popup'):
        clicked_building = map_data['last_object_clicked_popup']
        st.success(f"📍 Selected: {clicked_building}")

    if route_details:
        st.info(
            f"🧭 Route from **{route_details['from']}** to **{route_details['to']}** · "
            f"{route_details['distance_km']:.2f} km · 🚶 {route_details['walk_time_minutes']} min walk"
        )

    # Predictive Flow
    if predictions:
        st.divider()
        st.subheader("🔮 Predictive Flow")
        time_slots = list(predictions.keys())
        selected_slot = st.selectbox("Plan ahead:", time_slots, index=0, key="prediction_slot")

        slot_predictions = predictions.get(selected_slot, [])
        if slot_predictions:
            for rec in slot_predictions:
                building = building_lookup.get(rec.get("building"))
                if not building:
                    continue

                predicted_occ = rec.get("predicted_occupancy", 0)
                walk_time = rec.get("walk_time_minutes")
                confidence = rec.get("confidence", "High")
                note = rec.get("note", "")
                best_time = rec.get("best_time", selected_slot)

                st.markdown(f"**{building['name']}** · {best_time} · {confidence} confidence")
                if walk_time is not None:
                    st.caption(f"🚶 Approx. {walk_time} min walk")
                st.progress(min(1.0, predicted_occ / 100))
                st.caption(f"Predicted occupancy: {predicted_occ:.0f}%")
                if note:
                    st.caption(f"💡 {note}")

    # Admin view
    if st.session_state.user_role == 'admin':
        st.divider()
        st.subheader("🛠️ Admin Overview")
        open_issues = [issue for issue in issues if issue.get("status") == "open"]
        high_severity = [issue for issue in open_issues if issue.get("severity") == "high"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Open Issues", len(open_issues))
        col2.metric("High Severity", len(high_severity))
        col3.metric("Total Reports", len(issues))

    # Report Issue Modal
    if report_issue:
        st.session_state.show_report_form = True
    
    if st.session_state.get('show_report_form', False):
        with st.expander("📝 Report an Issue", expanded=True):
            with st.form("issue_report_form"):
                building_options = {b['name']: b['id'] for b in buildings}
                building_name = st.selectbox("Building", options=list(building_options.keys()))
                
                issue_type = st.selectbox("Issue Type", options=["outlet", "accessibility", "crowd", "temperature", "other"])
                
                description = st.text_area("Description", placeholder="Describe the issue in detail...")
                
                severity = st.select_slider("Severity", options=["low", "medium", "high"], value="medium")
                
                submitted = st.form_submit_button("Submit Report", type="primary")
                
                if submitted:
                    if description.strip():
                        st.success("✅ Report submitted successfully!")
                        st.session_state.show_report_form = False
                        st.rerun()
                    else:
                        st.warning("Please provide a description of the issue.")
    
    # Accessibility information
    if show_accessibility:
        st.header("♿ Accessibility Information")
        accessibility_data = load_accessibility()
        
        for acc in accessibility_data:
            building_name = building_names.get(acc['building_id'], acc['building_id'])
            with st.expander(f"🏛️ {building_name}"):
                st.write(f"**Elevators:** {acc['elevators']}")
                st.write(f"**Accessible Washrooms:** {acc['accessible_washrooms']}")
                st.write(f"**Notes:** {acc['notes']}")

if __name__ == "__main__":
    main()