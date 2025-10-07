from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import googlemaps
import searoute as sr
from geopy.distance import geodesic
import math
import asyncio
import requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Load environment variables
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Google Maps client
GOOGLE_MAPS_API_KEY = "AIzaSyBJv0JGQimJcxiuv7AP3YlfWLUJqQkEkq0"
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Load airports data
airports_path = ROOT_DIR.parent / 'airports.json'
with open(airports_path, 'r') as f:
    AIRPORTS_DATA = json.load(f)

# Create the main app without a prefix
app = FastAPI(title="Transport Emission Calculator API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class Good(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: float
    unit: str  # kg, tons, etc.
    ghg_category: str  # upstream, downstream, company_owned
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GoodCreate(BaseModel):
    name: str
    quantity: float
    unit: str
    ghg_category: str  # upstream, downstream, company_owned

class Location(BaseModel):
    address: str
    latitude: float
    longitude: float
    type: str = "general"  # general, airport, port, railway_station

class TransportLeg(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_location: Location
    to_location: Location
    transport_mode: str  # road, rail, air, water
    vehicle_type: str
    distance_km: float
    cost_type: str  # per_kg, per_ton, total
    cost_value: float
    manual_distance: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransportLegCreate(BaseModel):
    from_location: Location
    to_location: Location
    transport_mode: str
    vehicle_type: str
    cost_type: str
    cost_value: float
    manual_distance: Optional[float] = None

class EmissionFactor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transport_mode: str
    vehicle_type: str
    emission_factor: float
    unit: str  # kgCO2/tonne-km, gCO2/kg-km, etc.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmissionFactorCreate(BaseModel):
    transport_mode: str
    vehicle_type: str
    emission_factor: float
    unit: str

class Shipment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    good: Good
    transport_legs: List[TransportLeg]
    total_distance: float
    total_cost: float
    total_emissions: float
    upstream_emissions: float = 0.0
    downstream_emissions: float = 0.0
    company_owned_emissions: float = 0.0
    upstream_cost: float = 0.0
    downstream_cost: float = 0.0
    company_owned_cost: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ShipmentCreate(BaseModel):
    good: Good
    transport_legs: List[TransportLegCreate]

class DistanceCalculationRequest(BaseModel):
    from_location: Location
    to_location: Location
    transport_mode: str

class TripAnalyticsRequest(BaseModel):
    time_period: str  # "7days", "30days", "2months", "6months", "1year"

# Helper functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def find_nearest_port(latitude, longitude, max_distance=500):
    """Find nearest major sea port coordinates"""
    # Major global ports coordinates
    major_ports = [
        {"name": "Shanghai", "lat": 31.2304, "lng": 121.4737},
        {"name": "Singapore", "lat": 1.2966, "lng": 103.7764},
        {"name": "Rotterdam", "lat": 51.9225, "lng": 4.4792},
        {"name": "Antwerp", "lat": 51.2194, "lng": 4.4025},
        {"name": "Hamburg", "lat": 53.5511, "lng": 9.9937},
        {"name": "Los Angeles", "lat": 33.7361, "lng": -118.2639},
        {"name": "Long Beach", "lat": 33.7701, "lng": -118.2137},
        {"name": "New York", "lat": 40.6700, "lng": -74.0458},
        {"name": "Hong Kong", "lat": 22.2793, "lng": 114.1628},
        {"name": "Busan", "lat": 35.0951, "lng": 129.0756},
        {"name": "Guangzhou", "lat": 23.0965, "lng": 113.3212},
        {"name": "Qingdao", "lat": 36.0671, "lng": 120.3826},
        {"name": "Dubai", "lat": 25.2769, "lng": 55.2962},
        {"name": "Tianjin", "lat": 39.0851, "lng": 117.1995},
        {"name": "Port Klang", "lat": 3.0048, "lng": 101.3918},
        {"name": "Kaohsiung", "lat": 22.6273, "lng": 120.3014},
        {"name": "Dalian", "lat": 38.9140, "lng": 121.6147},
        {"name": "Valencia", "lat": 39.4561, "lng": -0.3545},
        {"name": "Yokohama", "lat": 35.4437, "lng": 139.6380},
        {"name": "Bremen", "lat": 53.0793, "lng": 8.8017},
        {"name": "Jawaharlal Nehru Port", "lat": 18.9647, "lng": 72.9505},  # Mumbai
        {"name": "Chennai Port", "lat": 13.1067, "lng": 80.3066},
        {"name": "Kolkata Port", "lat": 22.5675, "lng": 88.3496},
        {"name": "Cochin Port", "lat": 9.9667, "lng": 76.2667},
        {"name": "Visakhapatnam Port", "lat": 17.6868, "lng": 83.2185},
        {"name": "Kandla Port", "lat": 23.0333, "lng": 70.2167},
        {"name": "Paradip Port", "lat": 20.2644, "lng": 86.6069},
    ]
    
    nearest_port = None
    min_distance = float('inf')
    
    for port in major_ports:
        distance = haversine_distance(latitude, longitude, port["lat"], port["lng"])
        if distance < min_distance and distance <= max_distance:
            min_distance = distance
            nearest_port = port
    
    if nearest_port:
        return nearest_port["lng"], nearest_port["lat"]  # Note: longitude first for searoute
    else:
        # Return original coordinates if no nearby port found
        return longitude, latitude

async def calculate_distance(from_location: Location, to_location: Location, transport_mode: str) -> float:
    """Calculate distance based on transport mode with improved accuracy"""
    
    if transport_mode == "road":
        try:
            # Use Google Maps Distance Matrix API for road distance
            result = gmaps.distance_matrix(
                origins=[(from_location.latitude, from_location.longitude)],
                destinations=[(to_location.latitude, to_location.longitude)],
                mode="driving",
                units="metric",
                avoid="tolls"
            )
            
            if result['status'] == 'OK' and result['rows'][0]['elements'][0]['status'] == 'OK':
                distance_m = result['rows'][0]['elements'][0]['distance']['value']
                return distance_m / 1000  # Convert to kilometers
            else:
                # Fallback to straight-line distance
                return haversine_distance(
                    from_location.latitude, from_location.longitude,
                    to_location.latitude, to_location.longitude
                )
        except Exception as e:
            logging.error(f"Google Maps API error: {e}")
            return haversine_distance(
                from_location.latitude, from_location.longitude,
                to_location.latitude, to_location.longitude
            )
    
    elif transport_mode == "rail":
        try:
            # Try Google Directions API for more accurate train routes
            directions_result = gmaps.directions(
                origin=(from_location.latitude, from_location.longitude),
                destination=(to_location.latitude, to_location.longitude),
                mode="transit",
                transit_mode=["rail"],
                units="metric"
            )
            
            if directions_result and len(directions_result) > 0:
                route = directions_result[0]
                if 'legs' in route:
                    total_distance = 0
                    for leg in route['legs']:
                        if 'distance' in leg:
                            total_distance += leg['distance']['value']
                    if total_distance > 0:
                        return total_distance / 1000  # Convert to kilometers
            
            # Fallback: try distance matrix with transit
            result = gmaps.distance_matrix(
                origins=[(from_location.latitude, from_location.longitude)],
                destinations=[(to_location.latitude, to_location.longitude)],
                mode="transit",
                transit_mode="train",
                units="metric"
            )
            
            if result['status'] == 'OK' and result['rows'][0]['elements'][0]['status'] == 'OK':
                distance_m = result['rows'][0]['elements'][0]['distance']['value']
                return distance_m / 1000
            else:
                # Final fallback: straight-line distance * rail factor (typically 1.2-1.3)
                straight_distance = haversine_distance(
                    from_location.latitude, from_location.longitude,
                    to_location.latitude, to_location.longitude
                )
                return straight_distance * 1.25  # Rail routes are usually 25% longer than straight line
                
        except Exception as e:
            logging.error(f"Google Maps transit API error: {e}")
            straight_distance = haversine_distance(
                from_location.latitude, from_location.longitude,
                to_location.latitude, to_location.longitude
            )
            return straight_distance * 1.25
    
    elif transport_mode == "water":
        try:
            # Find nearest major ports for more accurate sea route calculation
            from_port = find_nearest_port(from_location.latitude, from_location.longitude)
            to_port = find_nearest_port(to_location.latitude, to_location.longitude)
            
            # Use searoute for sea distance calculation
            route = sr.searoute(from_port, to_port)
            
            if route and hasattr(route, 'properties') and 'length' in route.properties:
                sea_distance = route.properties['length']
                
                # Add distance from original points to nearest ports if they're different
                from_port_distance = 0
                to_port_distance = 0
                
                if (abs(from_port[1] - from_location.latitude) > 0.01 or 
                    abs(from_port[0] - from_location.longitude) > 0.01):
                    from_port_distance = haversine_distance(
                        from_location.latitude, from_location.longitude,
                        from_port[1], from_port[0]
                    )
                
                if (abs(to_port[1] - to_location.latitude) > 0.01 or 
                    abs(to_port[0] - to_location.longitude) > 0.01):
                    to_port_distance = haversine_distance(
                        to_location.latitude, to_location.longitude,
                        to_port[1], to_port[0]
                    )
                
                return sea_distance + from_port_distance + to_port_distance
            else:
                # Fallback to straight-line distance * sea factor
                straight_distance = haversine_distance(
                    from_location.latitude, from_location.longitude,
                    to_location.latitude, to_location.longitude
                )
                return straight_distance * 1.4  # Sea routes are usually 40% longer
                
        except Exception as e:
            logging.error(f"Searoute API error: {e}")
            # Fallback to straight-line distance * sea factor
            straight_distance = haversine_distance(
                from_location.latitude, from_location.longitude,
                to_location.latitude, to_location.longitude
            )
            return straight_distance * 1.4
    
    elif transport_mode == "air":
        # Use Haversine formula for air distance (great circle distance)
        return haversine_distance(
            from_location.latitude, from_location.longitude,
            to_location.latitude, to_location.longitude
        )
    
    else:
        raise ValueError(f"Unknown transport mode: {transport_mode}")

# Routes for Goods
@api_router.post("/goods", response_model=Good)
async def create_good(good_data: GoodCreate):
    good_dict = good_data.dict()
    good = Good(**good_dict)
    prepared_data = prepare_for_mongo(good.dict())
    await db.goods.insert_one(prepared_data)
    return good

@api_router.get("/goods", response_model=List[Good])
async def get_goods():
    goods = await db.goods.find().to_list(1000)
    return [Good(**good) for good in goods]

@api_router.get("/goods/{good_id}", response_model=Good)
async def get_good(good_id: str):
    good = await db.goods.find_one({"id": good_id})
    if not good:
        raise HTTPException(status_code=404, detail="Good not found")
    return Good(**good)

# Routes for Emission Factors
@api_router.post("/emission-factors", response_model=EmissionFactor)
async def create_emission_factor(factor_data: EmissionFactorCreate):
    factor_dict = factor_data.dict()
    factor = EmissionFactor(**factor_dict)
    prepared_data = prepare_for_mongo(factor.dict())
    await db.emission_factors.insert_one(prepared_data)
    return factor

@api_router.get("/emission-factors", response_model=List[EmissionFactor])
async def get_emission_factors():
    factors = await db.emission_factors.find().to_list(1000)
    return [EmissionFactor(**factor) for factor in factors]

@api_router.put("/emission-factors/{factor_id}", response_model=EmissionFactor)
async def update_emission_factor(factor_id: str, factor_data: EmissionFactorCreate):
    factor_dict = factor_data.dict()
    factor_dict['id'] = factor_id
    factor = EmissionFactor(**factor_dict)
    prepared_data = prepare_for_mongo(factor.dict())
    
    result = await db.emission_factors.update_one(
        {"id": factor_id}, 
        {"$set": prepared_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Emission factor not found")
    
    return factor

@api_router.delete("/emission-factors/{factor_id}")
async def delete_emission_factor(factor_id: str):
    result = await db.emission_factors.delete_one({"id": factor_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Emission factor not found")
    return {"message": "Emission factor deleted successfully"}

# Distance calculation route
@api_router.post("/calculate-distance")
async def calculate_distance_endpoint(request: DistanceCalculationRequest):
    try:
        distance = await calculate_distance(
            request.from_location, 
            request.to_location, 
            request.transport_mode
        )
        return {"distance_km": distance}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Airport search route with faster response
@api_router.get("/airports/search")
async def search_airports(query: str = Query(..., min_length=1)):
    query = query.lower()
    matching_airports = []
    
    # Search through airports with priority scoring
    for airport in AIRPORTS_DATA:
        score = 0
        name = airport.get('name', '').lower()
        city = airport.get('city', '').lower()
        code = airport.get('code', '').lower()
        iata_code = airport.get('iata_code', '').lower()
        
        # Higher priority for exact matches
        if query == code or query == iata_code:
            score = 100
        elif query in code or query in iata_code:
            score = 90
        elif city.startswith(query):
            score = 80
        elif query in city:
            score = 70
        elif name.startswith(query):
            score = 60
        elif query in name:
            score = 50
        
        if score > 0:
            airport['search_score'] = score
            matching_airports.append(airport)
    
    # Sort by score (descending) and limit results
    matching_airports.sort(key=lambda x: x.get('search_score', 0), reverse=True)
    return matching_airports[:8]  # Return top 8 results for faster response

# Location search route with enhanced fallback and debugging
@api_router.get("/locations/search")
async def search_locations(query: str = Query(..., min_length=2), location_type: str = "general"):
    try:
        if location_type == "airport":
            return await search_airports(query)
        
        # Try Google Places API first
        try:
            places_result = gmaps.places(
                query=query,
                type='geocode'
            )
            
            locations = []
            for place in places_result.get('results', [])[:6]:
                geometry = place.get('geometry', {})
                if geometry and 'location' in geometry:
                    location = Location(
                        address=place.get('formatted_address', place.get('name', '')),
                        latitude=geometry['location']['lat'],
                        longitude=geometry['location']['lng'],
                        type=location_type
                    )
                    locations.append(location)
            
            if locations:
                return locations
                
        except Exception as places_error:
            logging.warning(f"Google Places API error: {places_error}")
            
        # Fallback: Try geocoding API
        try:
            geocode_result = gmaps.geocode(query)
            
            locations = []
            for place in geocode_result[:6]:
                geometry = place.get('geometry', {})
                if geometry and 'location' in geometry:
                    location = Location(
                        address=place.get('formatted_address', ''),
                        latitude=geometry['location']['lat'],
                        longitude=geometry['location']['lng'],
                        type=location_type
                    )
                    locations.append(location)
            
            if locations:
                return locations
                
        except Exception as geocode_error:
            logging.warning(f"Google Geocoding API error: {geocode_error}")
        
        # Final fallback: Return some common Indian cities for demo
        if any(city in query.lower() for city in ['mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata', 'pune', 'hyderabad', 'ahmedabad']):
            fallback_cities = {
                'mumbai': {'lat': 19.0760, 'lng': 72.8777, 'address': 'Mumbai, Maharashtra, India'},
                'delhi': {'lat': 28.7041, 'lng': 77.1025, 'address': 'New Delhi, Delhi, India'},
                'bangalore': {'lat': 12.9716, 'lng': 77.5946, 'address': 'Bangalore, Karnataka, India'},
                'chennai': {'lat': 13.0827, 'lng': 80.2707, 'address': 'Chennai, Tamil Nadu, India'},
                'kolkata': {'lat': 22.5726, 'lng': 88.3639, 'address': 'Kolkata, West Bengal, India'},
                'pune': {'lat': 18.5204, 'lng': 73.8567, 'address': 'Pune, Maharashtra, India'},
                'hyderabad': {'lat': 17.3850, 'lng': 78.4867, 'address': 'Hyderabad, Telangana, India'},
                'ahmedabad': {'lat': 23.0225, 'lng': 72.5714, 'address': 'Ahmedabad, Gujarat, India'}
            }
            
            locations = []
            for city, data in fallback_cities.items():
                if city in query.lower():
                    location = Location(
                        address=data['address'],
                        latitude=data['lat'],
                        longitude=data['lng'],
                        type=location_type
                    )
                    locations.append(location)
            
            return locations
        
        return []
        
    except Exception as e:
        logging.error(f"Location search error: {str(e)}")
        return []

# Shipment routes
@api_router.post("/shipments", response_model=Shipment)
async def create_shipment(shipment_data: ShipmentCreate):
    try:
        # Calculate distances and emissions for transport legs
        transport_legs = []
        total_distance = 0
        total_cost = 0
        total_emissions = 0
        
        # GHG category totals
        upstream_emissions = 0
        downstream_emissions = 0
        company_owned_emissions = 0
        upstream_cost = 0
        downstream_cost = 0
        company_owned_cost = 0
        
        good_quantity_kg = shipment_data.good.quantity
        if shipment_data.good.unit == "tons":
            good_quantity_kg *= 1000
        
        for leg_data in shipment_data.transport_legs:
            # Calculate distance
            if leg_data.manual_distance:
                distance = leg_data.manual_distance
                manual_distance = True
            else:
                distance = await calculate_distance(
                    leg_data.from_location,
                    leg_data.to_location,
                    leg_data.transport_mode
                )
                manual_distance = False
            
            # Create transport leg
            leg = TransportLeg(
                from_location=leg_data.from_location,
                to_location=leg_data.to_location,
                transport_mode=leg_data.transport_mode,
                vehicle_type=leg_data.vehicle_type,
                distance_km=distance,
                cost_type=leg_data.cost_type,
                cost_value=leg_data.cost_value,
                manual_distance=manual_distance
            )
            
            transport_legs.append(leg)
            total_distance += distance
            
            # Calculate cost
            if leg_data.cost_type == "per_kg":
                leg_cost = leg_data.cost_value * good_quantity_kg
            elif leg_data.cost_type == "per_ton":
                leg_cost = leg_data.cost_value * (good_quantity_kg / 1000)
            else:  # total
                leg_cost = leg_data.cost_value
            
            total_cost += leg_cost
            
            # Add to GHG category costs (based on good's category)
            if shipment_data.good.ghg_category == "upstream":
                upstream_cost += leg_cost
            elif shipment_data.good.ghg_category == "downstream":
                downstream_cost += leg_cost
            elif shipment_data.good.ghg_category == "company_owned":
                company_owned_cost += leg_cost
            
            # Calculate emissions (find matching emission factor)
            emission_factor_doc = await db.emission_factors.find_one({
                "transport_mode": leg_data.transport_mode,
                "vehicle_type": leg_data.vehicle_type
            })
            
            leg_emissions = 0
            if emission_factor_doc:
                emission_factor = emission_factor_doc['emission_factor']
                # Calculate emissions based on distance and weight
                if emission_factor_doc['unit'] == "kgCO2/tonne-km":
                    leg_emissions = emission_factor * (good_quantity_kg / 1000) * distance
                elif emission_factor_doc['unit'] == "gCO2/kg-km":
                    leg_emissions = (emission_factor / 1000) * good_quantity_kg * distance
                else:
                    # Default calculation
                    leg_emissions = emission_factor * (good_quantity_kg / 1000) * distance
                
                total_emissions += leg_emissions
                
                # Add to GHG category emissions (based on good's category)
                if shipment_data.good.ghg_category == "upstream":
                    upstream_emissions += leg_emissions
                elif shipment_data.good.ghg_category == "downstream":
                    downstream_emissions += leg_emissions
                elif shipment_data.good.ghg_category == "company_owned":
                    company_owned_emissions += leg_emissions
        
        # Create shipment
        shipment = Shipment(
            good=shipment_data.good,
            transport_legs=transport_legs,
            total_distance=total_distance,
            total_cost=total_cost,
            total_emissions=total_emissions,
            upstream_emissions=upstream_emissions,
            downstream_emissions=downstream_emissions,
            company_owned_emissions=company_owned_emissions,
            upstream_cost=upstream_cost,
            downstream_cost=downstream_cost,
            company_owned_cost=company_owned_cost
        )
        
        prepared_data = prepare_for_mongo(shipment.dict())
        await db.shipments.insert_one(prepared_data)
        
        return shipment
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Shipment creation error: {str(e)}")

@api_router.get("/shipments", response_model=List[Shipment])
async def get_shipments():
    shipments = await db.shipments.find().to_list(1000)
    
    # Handle backward compatibility for shipments without ghg_category
    processed_shipments = []
    for shipment in shipments:
        # Add default ghg_category if missing
        if 'good' in shipment and 'ghg_category' not in shipment['good']:
            shipment['good']['ghg_category'] = 'upstream'  # Default to upstream
        
        processed_shipments.append(Shipment(**shipment))
    
    return processed_shipments

class BulkDeleteRequest(BaseModel):
    shipment_ids: List[str]

@api_router.delete("/shipments/bulk")
async def bulk_delete_shipments(request: BulkDeleteRequest):
    try:
        result = await db.shipments.delete_many({"id": {"$in": request.shipment_ids}})
        return {"deleted_count": result.deleted_count, "message": f"Successfully deleted {result.deleted_count} shipments"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bulk delete error: {str(e)}")

# Trip analytics route
@api_router.post("/shipments/analytics")
async def get_trip_analytics(request: TripAnalyticsRequest):
    try:
        # Calculate date range based on time period
        end_date = datetime.now(timezone.utc)
        
        if request.time_period == "7days":
            start_date = end_date - timedelta(days=7)
        elif request.time_period == "30days":
            start_date = end_date - timedelta(days=30)
        elif request.time_period == "2months":
            start_date = end_date - timedelta(days=60)
        elif request.time_period == "6months":
            start_date = end_date - timedelta(days=180)
        elif request.time_period == "1year":
            start_date = end_date - timedelta(days=365)
        else:
            raise ValueError("Invalid time period")
        
        # Query shipments in date range
        shipments = await db.shipments.find({
            "created_at": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }).to_list(1000)
        
        # Calculate analytics
        total_shipments = len(shipments)
        total_cost = sum(float(s.get('total_cost', 0)) for s in shipments)
        total_emissions = sum(float(s.get('total_emissions', 0)) for s in shipments)
        total_distance = sum(float(s.get('total_distance', 0)) for s in shipments)
        
        # Group by goods for charts
        goods_data = {}
        for shipment in shipments:
            good_name = shipment.get('good', {}).get('name', 'Unknown')
            if good_name not in goods_data:
                goods_data[good_name] = {
                    'name': good_name,
                    'cost': 0,
                    'emissions': 0,
                    'distance': 0,
                    'count': 0
                }
            
            goods_data[good_name]['cost'] += float(shipment.get('total_cost', 0))
            goods_data[good_name]['emissions'] += float(shipment.get('total_emissions', 0))
            goods_data[good_name]['distance'] += float(shipment.get('total_distance', 0))
            goods_data[good_name]['count'] += 1
        
        return {
            "time_period": request.time_period,
            "total_shipments": total_shipments,
            "total_cost": round(total_cost, 2),
            "total_emissions": round(total_emissions, 2),
            "total_distance": round(total_distance, 2),
            "goods_breakdown": list(goods_data.values()),
            "average_cost_per_shipment": round(total_cost / total_shipments if total_shipments > 0 else 0, 2),
            "average_emissions_per_shipment": round(total_emissions / total_shipments if total_shipments > 0 else 0, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analytics error: {str(e)}")

# Scatter plot analytics for GHG categories
@api_router.get("/shipments/scatter-analytics")
async def get_scatter_plot_analytics():
    try:
        shipments = await db.shipments.find().to_list(1000)
        
        scatter_data = {
            "upstream": [],
            "downstream": [],
            "company_owned": [],
            "totals": {
                "upstream_emissions": 0,
                "downstream_emissions": 0,
                "company_owned_emissions": 0,
                "total_emissions": 0
            }
        }
        
        # Process each shipment for scatter plot data
        for shipment in shipments:
            good_name = shipment.get('good', {}).get('name', 'Unknown')
            quantity = shipment.get('good', {}).get('quantity', 0)
            ghg_category = shipment.get('good', {}).get('ghg_category', 'upstream')

            # Track total cost and emissions for this shipment
            total_cost = 0
            total_emissions = 0

            for leg in shipment.get('transport_legs', []):
                if ghg_category in ["upstream", "downstream", "company_owned"]:
                    # Calculate leg-specific cost and emissions
                    leg_cost = leg.get('cost_value', 0)
                    
                    # Get emission factor for this leg
                    emission_factor_doc = await db.emission_factors.find_one({
                        "transport_mode": leg.get('transport_mode'),
                        "vehicle_type": leg.get('vehicle_type')
                    })
                    
                    leg_emissions = 0
                    if emission_factor_doc:
                        emission_factor = emission_factor_doc['emission_factor']
                        distance = leg.get('distance_km', 0)
                        good_quantity_kg = quantity
                        if shipment.get('good', {}).get('unit') == 'tons':
                            good_quantity_kg *= 1000

                        if emission_factor_doc['unit'] == "kgCO2/tonne-km":
                            leg_emissions = emission_factor * (good_quantity_kg / 1000) * distance
                        elif emission_factor_doc['unit'] == "gCO2/kg-km":
                            leg_emissions = (emission_factor / 1000) * good_quantity_kg * distance
                        else:
                            leg_emissions = emission_factor * (good_quantity_kg / 1000) * distance

                    total_cost += leg_cost
                    total_emissions += leg_emissions

            # Add shipment data to the correct category based on good's ghg_category
            if total_cost > 0 or total_emissions > 0:
                scatter_data[ghg_category].append({
                    "good_name": good_name,
                    "cost": round(total_cost, 2),
                    "emissions": round(total_emissions, 2),
                    "quantity": quantity,
                    "shipment_id": shipment.get('id')
                })

                # Add to totals
                scatter_data["totals"][f"{ghg_category}_emissions"] += total_emissions
        
        # Calculate total emissions
        scatter_data["totals"]["total_emissions"] = (
            scatter_data["totals"]["upstream_emissions"] + 
            scatter_data["totals"]["downstream_emissions"] + 
            scatter_data["totals"]["company_owned_emissions"]
        )
        
        # Round totals
        for key, value in scatter_data["totals"].items():
            scatter_data["totals"][key] = round(value, 2)
        
        return scatter_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scatter analytics error: {str(e)}")

# Clear all data endpoint (for reset)
@api_router.post("/reset-all-data")
async def reset_all_data():
    try:
        # Clear all shipments
        await db.shipments.delete_many({})
        
        return {"message": "All data has been reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Reset error: {str(e)}")

# Initialize default emission factors
@api_router.post("/init-emission-factors")
async def initialize_emission_factors():
    """Initialize default emission factors based on Indian GHG protocols"""
    
    default_factors = [
        # Road transport
        {"transport_mode": "road", "vehicle_type": "Small Car", "emission_factor": 0.15, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "road", "vehicle_type": "Medium Car", "emission_factor": 0.18, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "road", "vehicle_type": "Large Car", "emission_factor": 0.22, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "road", "vehicle_type": "Light Truck", "emission_factor": 0.65, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "road", "vehicle_type": "Heavy Truck", "emission_factor": 0.18, "unit": "kgCO2/tonne-km"},
        
        # Rail transport
        {"transport_mode": "rail", "vehicle_type": "Electric Train", "emission_factor": 0.03, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "rail", "vehicle_type": "Diesel Train", "emission_factor": 0.06, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "rail", "vehicle_type": "Freight Train", "emission_factor": 0.04, "unit": "kgCO2/tonne-km"},
        
        # Air transport
        {"transport_mode": "air", "vehicle_type": "Domestic Flight", "emission_factor": 0.85, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "air", "vehicle_type": "International Flight", "emission_factor": 0.75, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "air", "vehicle_type": "Cargo Flight", "emission_factor": 1.2, "unit": "kgCO2/tonne-km"},
        
        # Water transport
        {"transport_mode": "water", "vehicle_type": "Container Ship", "emission_factor": 0.015, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "water", "vehicle_type": "Bulk Carrier", "emission_factor": 0.012, "unit": "kgCO2/tonne-km"},
        {"transport_mode": "water", "vehicle_type": "Ferry", "emission_factor": 0.25, "unit": "kgCO2/tonne-km"},
    ]
    
    # Check if factors already exist
    existing_count = await db.emission_factors.count_documents({})
    if existing_count == 0:
        for factor_data in default_factors:
            factor = EmissionFactor(**factor_data)
            prepared_data = prepare_for_mongo(factor.dict())
            await db.emission_factors.insert_one(prepared_data)
        
        return {"message": f"Initialized {len(default_factors)} default emission factors"}
    else:
        return {"message": f"Emission factors already exist ({existing_count} factors found)"}

# AI Optimization Analysis
# Vehicle types by transport mode
@api_router.get("/vehicle-types/{transport_mode}")
async def get_vehicle_types(transport_mode: str):
    """Get available vehicle types for a transport mode"""
    factors = await db.emission_factors.find({"transport_mode": transport_mode}).to_list(1000)
    vehicle_types = list(set([factor['vehicle_type'] for factor in factors]))
    return {"vehicle_types": vehicle_types}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()