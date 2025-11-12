"""
Map utilities for rendering campus map with Folium
"""
import folium
from folium import plugins
import json
import math
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Color mapping for building status
STATUS_COLORS = {
    "quiet": "blue",
    "busy": "orange",
    "broken": "red"
}

# Icon mapping
STATUS_ICONS = {
    "quiet": "info-sign",
    "busy": "warning-sign",
    "broken": "remove-sign"
}

def load_buildings() -> List[Dict]:
    """Load building data from JSON file"""
    data_path = Path(__file__).parent.parent / "data" / "buildings.json"
    with open(data_path, 'r') as f:
        return json.load(f)

def load_accessibility() -> List[Dict]:
    """Load accessibility data from JSON file"""
    data_path = Path(__file__).parent.parent / "data" / "accessibility.json"
    with open(data_path, 'r') as f:
        return json.load(f)

def create_campus_map(
    center_lat: float = 49.2606,
    center_lon: float = -123.2460,
    zoom: int = 15,
    show_accessibility: bool = False,
    show_heatmap: bool = False,
    buildings: Optional[List[Dict]] = None
) -> folium.Map:
    """
    Create a Folium map with building markers
    
    Args:
        center_lat: Latitude for map center
        center_lon: Longitude for map center
        zoom: Initial zoom level
        show_accessibility: Whether to show accessibility markers
        show_heatmap: Whether to show occupancy heatmap
        buildings: Optional list of buildings to display (if None, loads all)
    
    Returns:
        Folium Map object
    """
    # Create base map with Street View as default (OpenStreetMap)
    campus_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles='OpenStreetMap',  # Street View as default
        prefer_canvas=False
    )
    
    # Add all tile layer options - IMPORTANT: Don't add the default layer again
    # Light mode
    folium.TileLayer('CartoDB positron', name='Light Mode', overlay=False, control=True).add_to(campus_map)
    
    # Dark mode
    folium.TileLayer('CartoDB dark_matter', name='Dark Mode', overlay=False, control=True).add_to(campus_map)
    
    # Satellite view using Esri World Imagery
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite View',
        overlay=False,
        control=True
    ).add_to(campus_map)
    
    # Load building data if not provided
    if buildings is None:
        buildings = load_buildings()
    
    accessibility_data = load_accessibility() if show_accessibility else []
    
    # Prepare heatmap data
    heat_data = []
    
    # Create accessibility lookup
    accessibility_lookup = {acc["building_id"]: acc for acc in accessibility_data}
    
    # Add building markers with enhanced popups
    for building in buildings:
        status = building.get("status", "quiet")
        color = STATUS_COLORS.get(status, "gray")
        icon = STATUS_ICONS.get(status, "info-sign")
        
        # Calculate occupancy percentage
        occupancy = building.get('occupancy', 0)
        capacity = building.get('capacity', 100)
        occupancy_pct = (occupancy / capacity * 100) if capacity > 0 else 0
        
        # Enhanced popup with styling - fixed text colors
        status_color_map = {"quiet": "#3b82f6", "busy": "#f59e0b", "broken": "#ef4444"}
        status_color = status_color_map.get(status, "#6b7280")
        
        popup_html = f"""
        <div style="width: 250px; font-family: Arial, sans-serif; color: #1f2937;">
            <h3 style="margin: 0 0 10px 0; color: #1e40af; font-weight: bold;">{building['name']}</h3>
            <div style="margin: 5px 0; color: #374151;">
                <strong style="color: #111827;">Status:</strong> 
                <span style="color: {status_color}; font-weight: bold;">{status.title()}</span>
            </div>
            <div style="margin: 5px 0; color: #374151;">
                <strong style="color: #111827;">Occupancy:</strong> 
                <span style="color: #111827;">{occupancy}/{capacity} ({occupancy_pct:.1f}%)</span>
            </div>
            <div style="margin: 5px 0;">
                <div style="background: #e5e7eb; border-radius: 5px; height: 20px; position: relative; border: 1px solid #d1d5db;">
                    <div style="background: {status_color}; height: 100%; width: {occupancy_pct}%; border-radius: 5px;"></div>
                </div>
            </div>
            <div style="margin-top: 10px; font-size: 0.9em; color: #6b7280;">
                <strong style="color: #374151;">ID:</strong> <span style="color: #6b7280;">{building['id']}</span>
            </div>
        </div>
        """
        
        # Add marker with custom icon
        folium.Marker(
            location=[building['lat'], building['lon']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{building['name']} - {status.title()} ({occupancy_pct:.0f}%)",
            icon=folium.Icon(color=color, icon=icon, prefix='glyphicon')
        ).add_to(campus_map)
        
        # Add to heatmap data
        if show_heatmap:
            # Weight based on occupancy percentage
            weight = occupancy_pct / 100.0
            heat_data.append([building['lat'], building['lon'], weight])
        
        # Add accessibility markers if enabled
        if show_accessibility and building['id'] in accessibility_lookup:
            acc_info = accessibility_lookup[building['id']]
            for entrance in acc_info.get('wheelchair_entrances', []):
                folium.CircleMarker(
                    location=[entrance['lat'], entrance['lon']],
                    radius=10,
                    popup=folium.Popup(
                        f"♿ <strong>{entrance['description']}</strong>",
                        max_width=200
                    ),
                    tooltip="♿ Accessible Entrance",
                    color='#10b981',
                    fill=True,
                    fillColor='#10b981',
                    fillOpacity=0.7,
                    weight=2
                ).add_to(campus_map)
    
    # Add heatmap layer if enabled
    if show_heatmap and heat_data:
        plugins.HeatMap(
            heat_data,
            min_opacity=0.2,
            max_zoom=18,
            radius=25,
            blur=15,
            gradient={0.2: 'blue', 0.4: 'cyan', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red'}
        ).add_to(campus_map)
    
    # Add enhanced legend with dark text
    legend_html = """
    <div style="position: absolute; 
                bottom: 20px; right: 20px; width: 220px; 
                background-color: rgba(255, 255, 255, 0.95); border: 2px solid #e5e7eb; border-radius: 8px; 
                z-index: 9999; font-size: 14px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                pointer-events: none;">
      <h4 style="margin: 0 0 10px 0; color: #111827; font-weight: bold;">Building Status</h4>
      <p style="margin: 5px 0; color: #374151;">
        <span style="font-size: 18px;">🔵</span> 
        <strong style="color: #111827;">Quiet</strong> 
        <span style="color: #6b7280;">- Low occupancy</span>
      </p>
      <p style="margin: 5px 0; color: #374151;">
        <span style="font-size: 18px;">🟠</span> 
        <strong style="color: #111827;">Busy</strong> 
        <span style="color: #6b7280;">- High occupancy</span>
      </p>
      <p style="margin: 5px 0; color: #374151;">
        <span style="font-size: 18px;">🔴</span> 
        <strong style="color: #111827;">Issues</strong> 
        <span style="color: #6b7280;">- Needs attention</span>
      </p>
    </div>
    """
    campus_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control with all base layers
    folium.LayerControl(
        position='topright',
        collapsed=False,
        autoZIndex=True
    ).add_to(campus_map)
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(campus_map)
    
    # Add measure tool
    plugins.MeasureControl().add_to(campus_map)
    
    return campus_map

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def get_smart_recommendations(current_building_id: str, buildings: List[Dict], max_recommendations: int = 3) -> List[Dict]:
    """
    Get smart recommendations for quiet alternative buildings
    
    Args:
        current_building_id: ID of the building user is currently at
        buildings: List of all buildings
        max_recommendations: Maximum number of recommendations to return
    
    Returns:
        List of recommended buildings with distance and walk time
    """
    # Find current building
    current_building = next((b for b in buildings if b['id'] == current_building_id), None)
    if not current_building:
        return []
    
    current_lat = current_building['lat']
    current_lon = current_building['lon']
    
    # Find quiet buildings with occupancy < 50%
    recommendations = []
    for building in buildings:
        if building['id'] == current_building_id:
            continue
        
        occupancy_pct = (building.get('occupancy', 0) / building.get('capacity', 100) * 100) if building.get('capacity', 100) > 0 else 0
        
        # Only recommend quiet buildings with low occupancy
        if building.get('status') == 'quiet' and occupancy_pct < 50:
            distance_km = calculate_distance(
                current_lat, current_lon,
                building['lat'], building['lon']
            )
            
            # Estimate walk time (average walking speed: 5 km/h)
            walk_time_minutes = int((distance_km / 5) * 60)
            
            recommendations.append({
                'building': building,
                'distance_km': round(distance_km, 2),
                'walk_time_minutes': walk_time_minutes,
                'occupancy_pct': round(occupancy_pct, 1)
            })
    
    # Sort by distance (closest first)
    recommendations.sort(key=lambda x: x['distance_km'])
    
    return recommendations[:max_recommendations]

def update_building_status(building_id: str, status: str, reports: List[Dict]) -> None:
    """
    Update building status based on recent reports
    
    Args:
        building_id: Building ID to update
        status: New status
        reports: List of reports to analyze
    """
    # This would typically update the buildings.json file
    # For now, it's handled in the main app
    pass


