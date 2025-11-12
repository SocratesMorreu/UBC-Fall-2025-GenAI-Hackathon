"""
Local AI Chatbot for CampusFlow
Provides intelligent, context-aware responses without requiring AWS Bedrock
Enhanced with web search for real-world data
"""
import json
import math
import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

try:
    from web_search import WebSearch
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    WebSearch = None

try:
    from ai_api_client import AIClient
    AI_API_AVAILABLE = True
except ImportError:
    AI_API_AVAILABLE = False
    AIClient = None


class LocalAIChatbot:
    """Local AI chatbot that provides intelligent campus recommendations"""
    
    def __init__(self):
        self.buildings = self._load_buildings()
        self.accessibility_data = self._load_accessibility()
        self.predictions = self._load_predictions()
        # Initialize web search if available
        if WEB_SEARCH_AVAILABLE and WebSearch:
            self.web_search = WebSearch()
        else:
            self.web_search = None
        # Initialize AI API client if available
        if AI_API_AVAILABLE and AIClient:
            self.ai_client = AIClient()
        else:
            self.ai_client = None
    
    def _load_buildings(self) -> List[Dict]:
        """Load building data"""
        try:
            data_path = Path(__file__).parent.parent / "data" / "buildings.json"
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _load_accessibility(self) -> List[Dict]:
        """Load accessibility data"""
        try:
            data_path = Path(__file__).parent.parent / "data" / "accessibility.json"
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _load_predictions(self) -> Dict[str, List[Dict]]:
        """Load predictive occupancy data"""
        try:
            data_path = Path(__file__).parent.parent / "data" / "predictions.json"
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers"""
        R = 6371  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    def find_building_by_name(self, query: str) -> Optional[Dict]:
        """Find a building by name or ID from query"""
        query_lower = query.lower()
        for building in self.buildings:
            if (query_lower in building['name'].lower() or 
                query_lower in building['id'].lower() or
                building['id'].lower() in query_lower):
                return building
        return None
    
    def get_quiet_buildings(self, max_occupancy_pct: float = 50.0) -> List[Dict]:
        """Get buildings with low occupancy"""
        quiet = []
        for building in self.buildings:
            occupancy_pct = (building.get('occupancy', 0) / building.get('capacity', 100) * 100) if building.get('capacity', 100) > 0 else 0
            if occupancy_pct < max_occupancy_pct and building.get('status') != 'broken':
                quiet.append({
                    'building': building,
                    'occupancy_pct': round(occupancy_pct, 1)
                })
        return sorted(quiet, key=lambda x: x['occupancy_pct'])
    
    def get_accessible_buildings(self) -> List[Dict]:
        """Get buildings with good accessibility features"""
        accessible = []
        acc_lookup = {acc['building_id']: acc for acc in self.accessibility_data}
        
        for building in self.buildings:
            building_id = building['id']
            if building_id in acc_lookup:
                acc_info = acc_lookup[building_id]
                accessible.append({
                    'building': building,
                    'elevators': acc_info.get('elevators', 0),
                    'accessible_washrooms': acc_info.get('accessible_washrooms', 0),
                    'notes': acc_info.get('notes', '')
                })
        
        return sorted(accessible, key=lambda x: x['elevators'], reverse=True)
    
    def get_nearby_alternatives(self, current_building: Dict, max_distance_km: float = 1.0) -> List[Dict]:
        """Get nearby quiet alternatives to a building"""
        current_lat = current_building['lat']
        current_lon = current_building['lon']
        
        alternatives = []
        quiet_buildings = self.get_quiet_buildings()
        
        for item in quiet_buildings:
            building = item['building']
            if building['id'] == current_building['id']:
                continue
            
            distance_km = self.calculate_distance(
                current_lat, current_lon,
                building['lat'], building['lon']
            )
            
            if distance_km <= max_distance_km:
                walk_time = int((distance_km / 5) * 60)  # 5 km/h walking speed
                alternatives.append({
                    'building': building,
                    'distance_km': round(distance_km, 2),
                    'walk_time_minutes': walk_time,
                    'occupancy_pct': item['occupancy_pct']
                })
        
        return sorted(alternatives, key=lambda x: x['distance_km'])
    
    def _get_campus_context(self) -> str:
        """Get formatted campus context for AI"""
        context_parts = []
        
        # Building data
        context_parts.append("Campus Buildings (with current occupancy):")
        for building in self.buildings[:15]:  # Limit to avoid token limits
            occupancy_pct = (building.get('occupancy', 0) / building.get('capacity', 100) * 100) if building.get('capacity', 100) > 0 else 0
            context_parts.append(
                f"- {building['name']} ({building['id']}): {building.get('status', 'quiet')} status, "
                f"{occupancy_pct:.1f}% occupied ({building.get('occupancy', 0)}/{building.get('capacity', 100)}), "
                f"Type: {building.get('type', 'academic')}, Amenities: {', '.join(building.get('amenities', [])[:3])}"
            )
        
        # Accessibility data
        context_parts.append("\nAccessibility Information:")
        for acc in self.accessibility_data[:10]:
            building_name = next((b['name'] for b in self.buildings if b['id'] == acc['building_id']), acc['building_id'])
            context_parts.append(
                f"- {building_name}: {acc['elevators']} elevators, {acc['accessible_washrooms']} accessible washrooms. {acc['notes']}"
            )
        
        if self.predictions:
            context_parts.append("\nOccupancy Forecasts:")
            for slot, recs in list(self.predictions.items())[:4]:
                if not recs:
                    continue
                top = recs[0]
                building_name = next((b['name'] for b in self.buildings if b['id'] == top.get('building')), top.get('building'))
                context_parts.append(
                    f"- {slot}: {building_name} at ~{top.get('predicted_occupancy', 0)}% occupancy. "
                    f"Suggested window: {top.get('best_time', 'N/A')}."
                )
        
        return "\n".join(context_parts)
    
    def _extract_location_from_query(self, query: str) -> Optional[str]:
        """Attempt to extract a location from the user's query"""
        # Look for phrases like "weather in <location>" or "forecast for <location>"
        location_patterns = [
            r"(?:weather|temperature|forecast|rain|sunny|climate)\s+(?:in|at|for)\s+([a-zA-Z\s,]+)",
            r"(?:in|at|for)\s+([a-zA-Z\s,]+)\s+(?:weather|temperature|forecast)"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Remove trailing words like "today" or "now"
                location = re.sub(r"\b(today|now|currently|right now)\b", "", location, flags=re.IGNORECASE).strip()
                if location:
                    return location
        
        return None

    def _match_prediction_slot(self, query_lower: str) -> Optional[str]:
        """Match user query to a predictive time slot"""
        if not self.predictions:
            return None

        slot_keywords = {
            "morning": "Morning (7-11 AM)",
            "before class": "Morning (7-11 AM)",
            "pre-class": "Morning (7-11 AM)",
            "midday": "Midday (11 AM-2 PM)",
            "noon": "Midday (11 AM-2 PM)",
            "lunch": "Midday (11 AM-2 PM)",
            "afternoon": "Afternoon (2-6 PM)",
            "after class": "Afternoon (2-6 PM)",
            "evening": "Evening (6-10 PM)",
            "tonight": "Evening (6-10 PM)",
            "night": "Evening (6-10 PM)"
        }

        for keyword, slot in slot_keywords.items():
            if keyword in query_lower and slot in self.predictions:
                return slot

        time_match = re.search(r"\b(\d{1,2})\s*(am|pm)\b", query_lower)
        if time_match:
            hour = int(time_match.group(1)) % 12
            period = time_match.group(2)
            if period == "pm":
                hour += 12
            if 7 <= hour <= 10 and "Morning (7-11 AM)" in self.predictions:
                return "Morning (7-11 AM)"
            if 11 <= hour <= 13 and "Midday (11 AM-2 PM)" in self.predictions:
                return "Midday (11 AM-2 PM)"
            if 14 <= hour <= 17 and "Afternoon (2-6 PM)" in self.predictions:
                return "Afternoon (2-6 PM)"
            if 18 <= hour <= 22 and "Evening (6-10 PM)" in self.predictions:
                return "Evening (6-10 PM)"

        if any(keyword in query_lower for keyword in ["later", "predict", "forecast", "plan ahead", "best time"]):
            return next(iter(self.predictions.keys()), None)

        return None

    def _format_prediction_response(self, slot: str) -> Optional[str]:
        """Generate a natural language response for a prediction slot"""
        slot_predictions = self.predictions.get(slot)
        if not slot_predictions:
            return None

        heading = f"🔮 **Predicted study flow for {slot}:**\n\n"
        body_sections = []
        for rec in slot_predictions[:4]:
            building = next((b for b in self.buildings if b['id'] == rec.get('building')), None)
            if not building:
                continue
            building_name = building['name']
            occupancy = rec.get('predicted_occupancy', 0)
            walk_time = rec.get('walk_time_minutes')
            best_time = rec.get('best_time', slot)
            note = rec.get('note', '')
            confidence = rec.get('confidence', 'High')
            amenities = ", ".join(building.get('amenities', [])[:3])

            entry_lines = [
                f"**{building_name}** · {best_time} · {confidence} confidence",
                f"- Predicted occupancy: {occupancy:.0f}%"
            ]
            if walk_time is not None:
                entry_lines[-1] += f" · 🚶 {walk_time} min walk from IKB"
            if amenities:
                entry_lines.append(f"- Amenities: {amenities}")
            if note:
                entry_lines.append(f"- 💡 {note}")

            body_sections.append("\n".join(entry_lines))

        if not body_sections:
            return None

        return heading + "\n\n".join(body_sections) + "\n\n_Need another window? Ask me about morning, midday, afternoon, or evening plans!_"
    
    def chat(self, user_query: str) -> str:
        """
        Generate intelligent response to user query
        Uses AI API if available, otherwise falls back to local logic
        """
        query_lower = user_query.lower()
        
        # Try AI API first if available
        if self.ai_client and self.ai_client.provider:
            try:
                # Get campus context
                campus_context = self._get_campus_context()
                
                # Enhanced system prompt
                system_prompt = """You are a helpful, knowledgeable campus AI assistant for UBC (University of British Columbia). 
You provide detailed, comprehensive answers to student questions.

Key capabilities:
- Real-time building occupancy and study spot recommendations
- Campus navigation and building information
- Accessibility information (elevators, ramps, wheelchair access)
- Academic help (registration, courses, schedules)
- Campus services (dining, food options, amenities)
- General student support and guidance

Guidelines:
- Be friendly, conversational, and helpful
- Provide detailed, comprehensive answers
- Use the real-time occupancy data when recommending study spots
- Include specific building names, distances, and walk times when relevant
- Use emojis appropriately to make responses engaging
- If you don't have specific information, guide users to where they can find it
- For registration questions, mention Workday (not SSC) as the current system
- Always try to be as helpful and detailed as possible"""
                
                # Call AI API
                ai_response = self.ai_client.chat(
                    user_query=user_query,
                    context=campus_context,
                    system_prompt=system_prompt
                )
                
                if ai_response:
                    return ai_response
            except Exception as e:
                print(f"AI API error: {e}, falling back to local logic")
        
        # Fallback to local logic if AI API not available or fails
        
        # Check if user mentions being at a specific building
        current_building = None
        for building in self.buildings:
            building_id_lower = building['id'].lower()
            building_name_lower = building['name'].lower()
            
            # Check if building is mentioned in query
            if (building_id_lower in query_lower or 
                building_name_lower in query_lower or
                any(word in query_lower for word in building_name_lower.split())):
                # Check if user is "at" this building (more flexible matching)
                location_words = ['at', 'in', 'here', 'currently', 'stuck', 'stuck at', 'sitting at', 'studying at']
                if any(word in query_lower for word in location_words):
                    current_building = building
                    break
                # Also check if query mentions building is full/busy (implies user is there)
                if any(word in query_lower for word in ['full', 'busy', 'crowded', 'packed', 'no space']):
                    current_building = building
                    break
        
        # Study spot recommendations
        if any(word in query_lower for word in ['study', 'study spot', 'quiet', 'place to work', 'where can i study']):
            prediction_slot = self._match_prediction_slot(query_lower)
            if prediction_slot:
                prediction_response = self._format_prediction_response(prediction_slot)
                if prediction_response:
                    return prediction_response

            if current_building:
                occupancy_pct = (current_building.get('occupancy', 0) / current_building.get('capacity', 100) * 100) if current_building.get('capacity', 100) > 0 else 0
                
                if occupancy_pct >= 70 or current_building.get('status') == 'busy':
                    # Building is busy, suggest alternatives
                    alternatives = self.get_nearby_alternatives(current_building, max_distance_km=1.5)
                    
                    if alternatives:
                        # More conversational, Gen AI-like response
                        response = f"Oh no! **{current_building['name']}** is {occupancy_pct:.0f}% full right now - that's pretty crowded! 😅\n\n"
                        response += f"Don't worry though, I've got some great alternatives nearby that should be much quieter:\n\n"
                        
                        for i, alt in enumerate(alternatives[:3], 1):
                            building_name = alt['building']['name']
                            walk_time = alt['walk_time_minutes']
                            distance = alt['distance_km']
                            occupancy = alt['occupancy_pct']
                            
                        response += (
                            f"**{i}. {building_name}**\n"
                            f"   🚶 Just {walk_time} minutes away ({distance} km)\n"
                            f"   {occupancy}% occupied - much calmer! ✨\n\n"
                        )
                        
                        # Add a friendly closing
                        best_alt = alternatives[0]
                        response += (
                            f"**My top pick:** **{best_alt['building']['name']}** is only "
                            f"{best_alt['walk_time_minutes']} minutes away and at "
                            f"{best_alt['occupancy_pct']}% capacity – perfect for focused studying! 📚\n\n"
                            "Really sorry you couldn't find a spot at your first choice — hopefully one of these feels just right. "
                            "Need me to route you there or check evening availability?"
                        )
                        return response
                    else:
                        return f"**{current_building['name']}** is busy ({occupancy_pct:.0f}% full), but I couldn't find nearby quiet alternatives. You might want to check back later or try a different time."
                else:
                    return f"Great news! **{current_building['name']}** is currently {occupancy_pct:.0f}% full and should be a good spot for studying. Enjoy your study session! 📚"
            else:
                # General study spot recommendations
                quiet_buildings = self.get_quiet_buildings(max_occupancy_pct=50.0)
                
                if quiet_buildings:
                    response = "Here are the best quiet study spots on campus right now:\n\n"
                    # Use Irving K. Barber as the central reference point for distance estimates
                    reference_building = next((b for b in self.buildings if b['id'] == 'ikb'), None)
                    
                    for i, item in enumerate(quiet_buildings[:5], 1):
                        building = item['building']
                        response += f"**{i}. {building['name']}**\n"
                        response += f"   {item['occupancy_pct']}% occupied • {building.get('status', 'quiet').title()} status\n"
                        response += f"   Capacity: {building.get('occupancy', 0)}/{building.get('capacity', 100)} people\n"
                        
                        if reference_building:
                            distance_km = self.calculate_distance(
                                reference_building['lat'], reference_building['lon'],
                                building['lat'], building['lon']
                            )
                            walk_time = int((distance_km / 5) * 60)  # Average walking speed 5 km/h
                            response += f"   🚶 Approx. {walk_time} min walk from IKB ({distance_km:.2f} km)\n"
                        
                        amenities = building.get('amenities', [])
                        if amenities:
                            response += f"   ✨ Amenities: {', '.join(amenities[:3])}\n"
                        
                        response += "\n"
                    
                    response += "These buildings have the lowest occupancy and should be perfect for focused studying! 🎯"
                    return response
                else:
                    return "It looks like most buildings are busy right now. I'd recommend checking back in an hour or trying during off-peak hours (early morning or late evening)."
        
        # Predictive flow / planning queries
        elif self.predictions and any(word in query_lower for word in ['predict', 'prediction', 'forecast', 'later', 'best time', 'plan ahead', 'busy later', 'evening', 'morning', 'afternoon']):
            prediction_slot = self._match_prediction_slot(query_lower) or next(iter(self.predictions.keys()), None)
            if prediction_slot:
                prediction_response = self._format_prediction_response(prediction_slot)
                if prediction_response:
                    return prediction_response
            return "I'm still learning this pattern. Try asking me about study spots or predictions for a specific time of day (morning, midday, afternoon, evening)."
        
        # Accessibility queries
        elif any(word in query_lower for word in ['accessible', 'lift', 'elevator', 'wheelchair', 'access', 'ramp']):
            accessible_buildings = self.get_accessible_buildings()
            
            if accessible_buildings:
                response = "Here are the most accessible buildings on campus with elevators and wheelchair access:\n\n"
                
                for i, item in enumerate(accessible_buildings[:5], 1):
                    building = item['building']
                    response += f"**{i}. {building['name']}**\n"
                    response += f"   ♿ {item['elevators']} elevators • {item['accessible_washrooms']} accessible washrooms\n"
                    response += f"   {item['notes']}\n\n"
                
                response += "All these buildings have multiple elevators and are fully wheelchair accessible! ♿"
                return response
            else:
                return "I'm having trouble accessing the accessibility information right now. Please check with campus facilities for specific accessibility details."
        
        # Building-specific queries
        elif any(word in query_lower for word in ['ikb', 'life', 'scarfe', 'koerner', 'nest', 'sauder', 'buchanan']):
            building = self.find_building_by_name(user_query)
            
            if building:
                occupancy_pct = (building.get('occupancy', 0) / building.get('capacity', 100) * 100) if building.get('capacity', 100) > 0 else 0
                status = building.get('status', 'quiet')
                
                response = f"**{building['name']}** Information:\n\n"
                response += f"📊 **Current Status:** {status.title()}\n"
                response += f"👥 **Occupancy:** {building.get('occupancy', 0)}/{building.get('capacity', 100)} ({occupancy_pct:.0f}% full)\n"
                
                # Add accessibility info if available
                acc_info = next((acc for acc in self.accessibility_data if acc['building_id'] == building['id']), None)
                if acc_info:
                    response += f"♿ **Accessibility:** {acc_info.get('elevators', 0)} elevators, {acc_info.get('accessible_washrooms', 0)} accessible washrooms\n"
                    response += f"📝 **Notes:** {acc_info.get('notes', '')}\n"
                
                # Suggest alternatives if busy
                if occupancy_pct >= 70 or status == 'busy':
                    alternatives = self.get_nearby_alternatives(building, max_distance_km=1.5)
                    if alternatives:
                        response += f"\n💡 **Nearby Quiet Alternatives:**\n"
                        for alt in alternatives[:2]:
                            response += f"   • {alt['building']['name']} ({alt['walk_time_minutes']} min walk, {alt['occupancy_pct']}% full)\n"
                
                return response
            else:
                return "I couldn't find that building. Could you try rephrasing or check the building name?"
        
        # Full/busy building queries
        elif any(word in query_lower for word in ['full', 'busy', 'crowded', 'packed', 'no space']):
            if current_building:
                occupancy_pct = (current_building.get('occupancy', 0) / current_building.get('capacity', 100) * 100) if current_building.get('capacity', 100) > 0 else 0
                alternatives = self.get_nearby_alternatives(current_building, max_distance_km=1.5)
                
                if alternatives:
                    # More conversational response
                    response = f"Ah, I see **{current_building['name']}** is {occupancy_pct:.0f}% full - definitely crowded! 😓\n\n"
                    response += f"No worries, here are some great nearby alternatives that should have space:\n\n"
                    
                    for i, alt in enumerate(alternatives[:3], 1):
                        response += f"**{i}. {alt['building']['name']}**\n"
                        response += f"   🚶 Only {alt['walk_time_minutes']} minutes away ({alt['distance_km']} km)\n"
                        response += f"   {alt['occupancy_pct']}% occupied - way quieter! ✨\n\n"
                    
                    # Highlight the best option
                    best_alt = alternatives[0]
                    response += f"**💡 My recommendation:** Head to **{best_alt['building']['name']}** - it's just {best_alt['walk_time_minutes']} minutes away and only {best_alt['occupancy_pct']}% full. Perfect spot! 📍"
                    return response
                else:
                    return f"**{current_building['name']}** is busy ({occupancy_pct:.0f}% full), but I couldn't find nearby quiet alternatives within walking distance. You might want to wait a bit or try during off-peak hours (early morning or late evening)."
            else:
                # Find busy buildings and suggest alternatives
                busy_buildings = [b for b in self.buildings if b.get('status') == 'busy']
                if busy_buildings:
                    response = "Here are some busy buildings and their nearby quiet alternatives:\n\n"
                    for building in busy_buildings[:3]:
                        alternatives = self.get_nearby_alternatives(building, max_distance_km=1.0)
                        if alternatives:
                            alt = alternatives[0]
                            response += f"**{building['name']}** is busy → Try **{alt['building']['name']}** ({alt['walk_time_minutes']} min walk, {alt['occupancy_pct']}% full)\n\n"
                    return response
                else:
                    return "Most buildings seem to have space available right now!"
        
        # General help
        elif any(word in query_lower for word in ['help', 'what can you do', 'what do you do']):
            return """I'm your campus AI assistant! I can help you with:

📚 **Study Spots** - Find quiet buildings with low occupancy
♿ **Accessibility** - Locate buildings with elevators and wheelchair access
📍 **Building Info** - Get details about any campus building
🚶 **Alternatives** - If a building is full, I'll suggest nearby quiet options

Try asking me:
• "Find me a study spot"
• "I'm at IKB and it's full"
• "Where are accessible lifts?"
• "Tell me about Life Sciences Centre"

I use real-time occupancy data to give you the best recommendations! 🎯"""
        
        # Weather queries
        elif any(word in query_lower for word in ['weather', 'temperature', 'rain', 'sunny', 'forecast']):
            if self.web_search:
                location = self._extract_location_from_query(user_query) or "Vancouver, BC"
                weather_info = self.web_search.get_weather(location)
                if weather_info:
                    return (
                        f"🌤️ **Current Weather ({location}):**\n\n"
                        f"{weather_info}\n\n"
                        "*Tip: Provide a different city or campus location for more precise weather info.*"
                    )
                else:
                    return "I couldn't fetch the weather right now. You can check weather.gov, weather.com, or a local weather app for current conditions."
            else:
                return "Weather information is not available right now. Please check a weather service for current conditions."
        
        # Student academic questions
        elif any(word in query_lower for word in ['register', 'registration', 'enroll', 'enrollment', 'course', 'class', 'schedule', 'timetable']):
            if self.web_search:
                try:
                    web_info = self.web_search.get_general_info(f"UBC {user_query}")
                    if web_info:
                        return f"{web_info}\n\n💡 **Quick Tips:**\n• Registration typically opens in July for fall term\n• Check SSC (Student Service Centre) for your registration time\n• Have backup course options ready\n• Contact academic advising if you need help\n\n*For specific registration dates and procedures, check the UBC website or contact your faculty advisor.*"
                except Exception:
                    pass
            
            return """📚 **Course Registration Help:**

**General Process:**
1. Log into **Workday** (UBC's student information system)
2. Check your registration time in Workday
3. Prepare your course list with alternatives
4. Register on your assigned date/time through Workday
5. Pay tuition fees by the deadline

**Common Questions:**
• **When can I register?** - Check Workday for your specific registration date and time
• **What if a course is full?** - Join the waitlist in Workday or check for alternative sections
• **How many credits?** - Full-time is typically 9+ credits per term
• **How do I access Workday?** - Go to workday.ubc.ca and log in with your CWL

**Need Help?**
• Academic Advising Office
• Your faculty's student services
• Workday Support: workday.ubc.ca/help
• IT Help Desk for technical issues

**Workday Features:**
• Course registration and enrollment
• Academic planning and degree progress
• Financial information and tuition payment
• Personal information management

*For specific registration dates and procedures, check Workday or contact your faculty advisor directly.* 🎓"""
        
        # Food and dining questions
        elif any(word in query_lower for word in ['food', 'eat', 'dining', 'cafeteria', 'restaurant', 'cafe', 'coffee', 'lunch', 'dinner', 'breakfast']):
            food_buildings = [b for b in self.buildings if 'food' in str(b.get('amenities', [])).lower() or 
                            'dining' in str(b.get('amenities', [])).lower() or
                            'café' in str(b.get('amenities', [])).lower() or
                            'cafe' in str(b.get('amenities', [])).lower()]
            
            response = "🍽️ **Campus Dining Options:**\n\n"
            if food_buildings:
                for building in food_buildings[:8]:
                    response += f"**• {building['name']}**\n"
                    amenities = building.get('amenities', [])
                    food_amenities = [a for a in amenities if any(word in a.lower() for word in ['food', 'dining', 'café', 'cafe', 'restaurant'])]
                    if food_amenities:
                        response += f"  {', '.join(food_amenities)}\n"
                    response += f"  📍 {building.get('occupancy', 0)}/{building.get('capacity', 100)} people\n\n"
            
            response += "**Popular Spots:**\n"
            response += "• **AMS Nest** - Food court with multiple options\n"
            response += "• **Ponderosa Commons** - All-you-can-eat dining\n"
            response += "• **Orchard Commons** - Variety of cuisines\n"
            response += "• **Sauder Café** - Quick bites and coffee\n"
            response += "• **IKB Café** - Study-friendly café\n\n"
            response += "*Hours vary by location. Check individual dining halls for current hours and menus.*"
            return response
        
        # General knowledge queries (use web search)
        elif any(word in query_lower for word in ['what is', 'who is', 'tell me about', 'explain', 'how does', 'when is', 'where is', 'why', 'how to', 'how do i']):
            # Try web search first
            if self.web_search:
                try:
                    # Enhance query for better results
                    enhanced_query = user_query
                    if not any(word in query_lower for word in ['ubc', 'university', 'campus']):
                        enhanced_query = f"UBC {user_query}"
                    
                    web_info = self.web_search.get_general_info(enhanced_query)
                    if web_info:
                        # Add helpful context
                        response = f"{web_info}\n\n"
                        
                        # Add campus-specific tips if relevant
                        if any(word in query_lower for word in ['campus', 'university', 'building', 'study', 'student', 'library', 'class', 'course']):
                            response += "💡 **Campus Tip:** For more specific information about UBC facilities, services, or procedures, you can also:\n"
                            response += "• Visit the UBC website\n"
                            response += "• Contact Student Services\n"
                            response += "• Ask me about specific buildings or services\n\n"
                            response += "*I've searched the web for this information. For campus-specific details, feel free to ask me about specific buildings or facilities!*"
                        else:
                            response += "*Information sourced from web search.*"
                        
                        return response
                except Exception as e:
                    print(f"Web search error: {e}")
                    pass
            
            # Fallback with helpful guidance
            return f"""I'd love to help with that! Let me provide some guidance:

**For Campus-Specific Questions:**
• Building locations and occupancy - I can help! 🏛️
• Study spot recommendations - Ask me! 📚
• Accessibility information - I have details! ♿
• Campus facilities and services - I know the campus! 🎓

**Blended Knowledge:**
I combine real-time campus data with web search (DuckDuckGo or Google via SerpAPI) and, when available, GPT/Claude intelligence to answer broader questions like weather, news, or general knowledge.

**For General Questions:**
I can search the web for information, but for the most accurate and up-to-date details, I recommend:
• Checking the official UBC website
• Contacting relevant departments directly
• Visiting student services

**What I'm Great At:**
• Finding quiet study spots
• Building recommendations based on occupancy
• Accessibility information
• Campus navigation and facilities

Try asking me something like:
• "Find me a quiet study spot"
• "I'm at IKB and it's full - where should I go?"
• "Where are accessible lifts?"
• "Tell me about [building name]"

What would you like to know? 🤔"""
        
        # Default response
        else:
            # Try to extract building name and provide general info
            building = self.find_building_by_name(user_query)
            if building:
                occupancy_pct = (building.get('occupancy', 0) / building.get('capacity', 100) * 100) if building.get('capacity', 100) > 0 else 0
                return f"**{building['name']}** is currently {occupancy_pct:.0f}% full with a {building.get('status', 'quiet')} status. "
            
            # Try web search for general queries
            if self.web_search:
                try:
                    web_info = self.web_search.get_general_info(user_query)
                    if web_info:
                        return f"{web_info}\n\n*If you're asking about campus facilities, try being more specific (e.g., 'find me a study spot' or 'where is IKB')*"
                except Exception:
                    pass
            
            # Try web search for general queries
            if self.web_search:
                try:
                    # Try with UBC context
                    enhanced_query = f"UBC {user_query}" if "ubc" not in query_lower else user_query
                    web_info = self.web_search.get_general_info(enhanced_query)
                    if web_info and len(web_info) > 50:  # Only use if substantial info
                        return f"{web_info}\n\n*If you're asking about campus facilities, try being more specific (e.g., 'find me a study spot' or 'where is IKB')*"
                except Exception:
                    pass
            
            # Comprehensive help response
            return """👋 **Hi! I'm your Campus AI Assistant!**

I'm here to help with everything related to campus life. Here's what I can do:

**🏛️ Campus Navigation:**
• Find quiet study spots based on real-time occupancy
• Building recommendations when your current spot is full
• Accessibility information (elevators, ramps, etc.)
• Building details and amenities

**📚 Academic Help:**
• Course registration guidance
• Study spot recommendations
• Building information

**🍽️ Campus Services:**
• Dining locations and options
• Food court information
• Café locations

**🌐 General Information:**
• Weather updates
• Web search for questions
• General knowledge (with web search)

**💡 Example Questions:**
• "I'm at IKB and it's full, where should I go?"
• "Find me a quiet study spot"
• "Where are accessible lifts?"
• "Where can I get food on campus?"
• "How do I register for classes?"
• "What's the weather today?"
• "Tell me about [building name]"

**Just ask me anything - I'll do my best to help!** 🚀

What would you like to know? 🤔"""

