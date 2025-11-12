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

from map_utils import create_campus_map, load_buildings, load_accessibility
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
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_input' not in st.session_state:
    st.session_state.chat_input = ''

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
    
    .chat-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .chat-message {
        background: white;
        padding: 1rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    .chat-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-left-color: #764ba2;
    }
    
    .stTextArea>div>div>textarea {
        background-color: white !important;
        color: #1f2937 !important;
        border-radius: 0.75rem;
        border: 2px solid #e5e7eb;
    }
    
    .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        color: #1f2937 !important;
        background-color: white !important;
    }
    
    .stTextArea>div>div>textarea::placeholder {
        color: #9ca3af !important;
    }
    
    /* Ensure text input is visible */
    input[type="text"], textarea {
        color: #1f2937 !important;
        background-color: white !important;
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
    
    # Sidebar - AI Chatbot as main feature
    with st.sidebar:
        # AI Chatbot Section - Prominent Panel
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1.5rem; border-radius: 1rem; margin-bottom: 1.5rem;
                    box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
            <h2 style="color: white; margin: 0; text-align: center;">🤖 AI Assistant</h2>
            <p style="color: rgba(255,255,255,0.9); text-align: center; margin-top: 0.5rem; font-size: 0.9em;">
                Ask me anything about campus!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat input with better styling
        st.markdown("### 💡 I Can Help With")
        st.markdown(
            """
            - Find quiet study spots and building occupancy
            - Suggest alternative spaces when areas are busy
            - Share accessibility entrances, elevators, and amenities
            - Explain how to submit and track campus reports
            - Answer campus services, dining, and facility questions
            """,
            help="Focused on campus knowledge powered by our real-time data and reporting tools."
        )

        st.markdown("### 💬 Ask Your Question")
        chat_query = st.text_area(
            "",
            placeholder="Ask me anything! Examples:\n• 'I'm at IKB and it's full, where should I go?'\n• 'Find me a quiet study spot'\n• 'Where are accessible lifts?'\n• 'What's the weather today?'\n• 'How do I register for classes?'\n• 'Where can I get food on campus?'",
            key="chat_input_field",
            height=120,
            label_visibility="collapsed"
        )
        
        col_ask, col_clear = st.columns([2, 1])
        with col_ask:
            ask_button = st.button("🚀 Ask AI", type="primary", use_container_width=True, key="chat_submit")
        with col_clear:
            if st.button("🗑️", use_container_width=True, key="clear_chat", help="Clear chat history"):
                st.session_state.chat_history = []
                st.rerun()
        
        if ask_button and chat_query.strip():
            with st.spinner("🤔 Thinking..."):
                response = api_client.chat(chat_query)
                # Add to chat history
                st.session_state.chat_history.append({
                    "query": chat_query,
                    "response": response,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                st.rerun()
        
        # Display chat history in a scrollable container
        if st.session_state.chat_history:
            st.markdown("---")
            st.markdown("### 💬 Conversation History")
            # Show most recent first
            for i, chat in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10
                with st.container():
                    # User message
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.5rem;
                                color: white;">
                        <div style="font-size: 0.7em; opacity: 0.9; margin-bottom: 0.25rem;">{chat['timestamp']} • You</div>
                        <div style="font-weight: 500; color: white;">{chat['query']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # AI response
                    st.markdown(f"""
                    <div style="background: white; padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.75rem;
                                border-left: 3px solid #667eea; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-size: 0.7em; color: #6b7280; margin-bottom: 0.25rem;">AI Assistant</div>
                        <div style="color: #1f2937; white-space: pre-wrap; line-height: 1.6;">{chat['response']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            show_trends = st.button("📈 Trends", use_container_width=True)
        with col2:
            report_issue = st.button("📝 Report", use_container_width=True)
        
        st.divider()
        
        # Map options (minimal)
        st.markdown("### 🗺️ Map Options")
        show_accessibility = st.checkbox("View Accessibility", value=False)
        show_heatmap = st.checkbox("Show Occupancy Heatmap", value=False)
        
        st.divider()
        
        # Role toggle
        st.markdown("### 👤 View Mode")
        user_role = st.radio(
            "Select your role:",
            options=["👩‍🎓 Student View", "🧰 Admin View"],
            index=0 if st.session_state.user_role == 'student' else 1,
            key="role_selector",
            label_visibility="collapsed"
        )
        st.session_state.user_role = 'student' if "Student" in user_role else 'admin'
        
        st.divider()
        
        # Status legend
        st.markdown("### 📋 Status Legend")
        st.markdown("🔵 **Blue** = Quiet")
        st.markdown("🟠 **Orange** = Busy")
        st.markdown("🔴 **Red** = Broken/Issues")
        
        # Quick stats
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
    
    # No filters - show all buildings
    filtered_buildings = buildings.copy()
    
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

