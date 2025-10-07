#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime
import time

class TransportEmissionAPITester:
    def __init__(self, base_url="https://carbonroute.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.created_good_id = None
        self.created_emission_factor_id = None
        self.created_shipment_id = None

    def log_test(self, test_name, success, details="", error_msg=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED: {error_msg}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "error": error_msg
        })

    def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request with error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            return response
        except requests.exceptions.RequestException as e:
            return None, str(e)

    def test_health_check(self):
        """Test basic API connectivity"""
        # Use emission-factors endpoint as health check since there's no dedicated health endpoint
        response = self.make_request('GET', 'emission-factors')
        if response and response.status_code == 200:
            self.log_test("API Health Check", True, "API is accessible")
            return True
        else:
            error_msg = f"API not accessible - Status: {response.status_code if response else 'No response'}"
            self.log_test("API Health Check", False, error_msg=error_msg)
            return False

    def test_initialize_emission_factors(self):
        """Test emission factors initialization"""
        response = self.make_request('POST', 'init-emission-factors')
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Initialize Emission Factors", True, f"Response: {data.get('message', '')}")
            return True
        else:
            error_msg = f"Failed to initialize emission factors - Status: {response.status_code if response else 'No response'}"
            self.log_test("Initialize Emission Factors", False, error_msg=error_msg)
            return False

    def test_get_emission_factors(self):
        """Test getting emission factors"""
        response = self.make_request('GET', 'emission-factors')
        if response and response.status_code == 200:
            factors = response.json()
            if len(factors) > 0:
                self.log_test("Get Emission Factors", True, f"Found {len(factors)} emission factors")
                # Store first factor ID for later tests
                self.created_emission_factor_id = factors[0]['id']
                return True
            else:
                self.log_test("Get Emission Factors", False, error_msg="No emission factors found")
                return False
        else:
            error_msg = f"Failed to get emission factors - Status: {response.status_code if response else 'No response'}"
            self.log_test("Get Emission Factors", False, error_msg=error_msg)
            return False

    def test_create_good(self):
        """Test creating a good"""
        good_data = {
            "name": "Test Electronics",
            "type": "Fragile",
            "quantity": 100.0,
            "unit": "kg"
        }
        
        response = self.make_request('POST', 'goods', good_data)
        if response and response.status_code == 200:
            created_good = response.json()
            self.created_good_id = created_good['id']
            self.log_test("Create Good", True, f"Created good with ID: {self.created_good_id}")
            return True
        else:
            error_msg = f"Failed to create good - Status: {response.status_code if response else 'No response'}"
            if response:
                error_msg += f" - Response: {response.text}"
            self.log_test("Create Good", False, error_msg=error_msg)
            return False

    def test_get_goods(self):
        """Test getting goods"""
        response = self.make_request('GET', 'goods')
        if response and response.status_code == 200:
            goods = response.json()
            self.log_test("Get Goods", True, f"Found {len(goods)} goods")
            return True
        else:
            error_msg = f"Failed to get goods - Status: {response.status_code if response else 'No response'}"
            self.log_test("Get Goods", False, error_msg=error_msg)
            return False

    def test_get_good_by_id(self):
        """Test getting a specific good by ID"""
        if not self.created_good_id:
            self.log_test("Get Good by ID", False, error_msg="No good ID available for testing")
            return False
            
        response = self.make_request('GET', f'goods/{self.created_good_id}')
        if response and response.status_code == 200:
            good = response.json()
            self.log_test("Get Good by ID", True, f"Retrieved good: {good['name']}")
            return True
        else:
            error_msg = f"Failed to get good by ID - Status: {response.status_code if response else 'No response'}"
            self.log_test("Get Good by ID", False, error_msg=error_msg)
            return False

    def test_location_search(self):
        """Test location search functionality"""
        # Test general location search
        response = self.make_request('GET', 'locations/search', params={'query': 'New York', 'location_type': 'general'})
        if response and response.status_code == 200:
            locations = response.json()
            if len(locations) > 0:
                self.log_test("Location Search (General)", True, f"Found {len(locations)} locations")
            else:
                self.log_test("Location Search (General)", False, error_msg="No locations found")
                return False
        else:
            error_msg = f"Failed location search - Status: {response.status_code if response else 'No response'}"
            self.log_test("Location Search (General)", False, error_msg=error_msg)
            return False

        # Test airport search
        response = self.make_request('GET', 'airports/search', params={'query': 'JFK'})
        if response and response.status_code == 200:
            airports = response.json()
            if len(airports) > 0:
                self.log_test("Airport Search", True, f"Found {len(airports)} airports")
                return True
            else:
                self.log_test("Airport Search", False, error_msg="No airports found")
                return False
        else:
            error_msg = f"Failed airport search - Status: {response.status_code if response else 'No response'}"
            self.log_test("Airport Search", False, error_msg=error_msg)
            return False

    def test_vehicle_types(self):
        """Test getting vehicle types for transport modes"""
        transport_modes = ['road', 'rail', 'air', 'water']
        
        for mode in transport_modes:
            response = self.make_request('GET', f'vehicle-types/{mode}')
            if response and response.status_code == 200:
                vehicle_types = response.json()
                if len(vehicle_types.get('vehicle_types', [])) > 0:
                    self.log_test(f"Vehicle Types ({mode})", True, f"Found {len(vehicle_types['vehicle_types'])} vehicle types")
                else:
                    self.log_test(f"Vehicle Types ({mode})", False, error_msg="No vehicle types found")
                    return False
            else:
                error_msg = f"Failed to get vehicle types for {mode} - Status: {response.status_code if response else 'No response'}"
                self.log_test(f"Vehicle Types ({mode})", False, error_msg=error_msg)
                return False
        
        return True

    def test_distance_calculation(self):
        """Test distance calculation for different transport modes"""
        # Test locations (New York to Los Angeles)
        from_location = {
            "address": "New York, NY, USA",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "type": "general"
        }
        
        to_location = {
            "address": "Los Angeles, CA, USA", 
            "latitude": 34.0522,
            "longitude": -118.2437,
            "type": "general"
        }

        transport_modes = ['road', 'rail', 'air', 'water']
        
        for mode in transport_modes:
            distance_data = {
                "from_location": from_location,
                "to_location": to_location,
                "transport_mode": mode
            }
            
            response = self.make_request('POST', 'calculate-distance', distance_data)
            if response and response.status_code == 200:
                result = response.json()
                distance = result.get('distance_km', 0)
                if distance > 0:
                    self.log_test(f"Distance Calculation ({mode})", True, f"Distance: {distance:.2f} km")
                else:
                    self.log_test(f"Distance Calculation ({mode})", False, error_msg="Distance is 0")
                    return False
            else:
                error_msg = f"Failed distance calculation for {mode} - Status: {response.status_code if response else 'No response'}"
                if response:
                    error_msg += f" - Response: {response.text}"
                self.log_test(f"Distance Calculation ({mode})", False, error_msg=error_msg)
                return False
        
        return True

    def test_indian_route_distance_calculation(self):
        """Test distance calculation for Indian routes as specified in requirements"""
        # Test the specific routes mentioned in requirements
        test_routes = [
            {
                "name": "Mumbai to Delhi",
                "from": {"address": "Mumbai, Maharashtra, India", "latitude": 19.0760, "longitude": 72.8777, "type": "general"},
                "to": {"address": "New Delhi, Delhi, India", "latitude": 28.7041, "longitude": 77.1025, "type": "general"},
                "mode": "road"
            },
            {
                "name": "Delhi to Bangalore", 
                "from": {"address": "New Delhi, Delhi, India", "latitude": 28.7041, "longitude": 77.1025, "type": "general"},
                "to": {"address": "Bangalore, Karnataka, India", "latitude": 12.9716, "longitude": 77.5946, "type": "general"},
                "mode": "rail"
            },
            {
                "name": "Bangalore to Chennai",
                "from": {"address": "Bangalore, Karnataka, India", "latitude": 12.9716, "longitude": 77.5946, "type": "general"},
                "to": {"address": "Chennai, Tamil Nadu, India", "latitude": 13.0827, "longitude": 80.2707, "type": "general"},
                "mode": "air"
            }
        ]
        
        for route in test_routes:
            distance_data = {
                "from_location": route["from"],
                "to_location": route["to"],
                "transport_mode": route["mode"]
            }
            
            response = self.make_request('POST', 'calculate-distance', distance_data)
            if response and response.status_code == 200:
                result = response.json()
                distance = result.get('distance_km', 0)
                if distance > 0:
                    self.log_test(f"Indian Route Distance ({route['name']} - {route['mode']})", True, f"Distance: {distance:.2f} km")
                else:
                    self.log_test(f"Indian Route Distance ({route['name']} - {route['mode']})", False, error_msg="Distance is 0")
                    return False
            else:
                error_msg = f"Failed Indian route distance calculation for {route['name']} - Status: {response.status_code if response else 'No response'}"
                if response:
                    error_msg += f" - Response: {response.text}"
                self.log_test(f"Indian Route Distance ({route['name']} - {route['mode']})", False, error_msg=error_msg)
                return False
        
        return True

    def test_create_single_leg_shipment(self):
        """Test creating a shipment with single transport leg"""
        if not self.created_good_id:
            self.log_test("Create Single Leg Shipment", False, error_msg="No good available for shipment creation")
            return False

        # Get the created good first
        good_response = self.make_request('GET', f'goods/{self.created_good_id}')
        if not good_response or good_response.status_code != 200:
            self.log_test("Create Single Leg Shipment", False, error_msg="Could not retrieve good for shipment")
            return False
        
        good = good_response.json()
        
        shipment_data = {
            "good": good,
            "transport_legs": [
                {
                    "from_location": {
                        "address": "New York, NY, USA",
                        "latitude": 40.7128,
                        "longitude": -74.0060,
                        "type": "general"
                    },
                    "to_location": {
                        "address": "Chicago, IL, USA",
                        "latitude": 41.8781,
                        "longitude": -87.6298,
                        "type": "general"
                    },
                    "transport_mode": "road",
                    "vehicle_type": "Heavy Truck",
                    "cost_type": "total",
                    "cost_value": 1500.0,
                    "manual_distance": None
                }
            ]
        }
        
        response = self.make_request('POST', 'shipments', shipment_data)
        if response and response.status_code == 200:
            shipment = response.json()
            self.created_shipment_id = shipment['id']
            self.log_test("Create Single Leg Shipment", True, f"Created shipment with ID: {self.created_shipment_id}")
            return True
        else:
            error_msg = f"Failed to create single leg shipment - Status: {response.status_code if response else 'No response'}"
            if response:
                error_msg += f" - Response: {response.text}"
            self.log_test("Create Single Leg Shipment", False, error_msg=error_msg)
            return False

    def test_create_multi_leg_shipment(self):
        """Test creating a multi-leg shipment as specified in requirements"""
        # Create the specific good for multi-leg testing
        electronics_good_data = {
            "name": "Electronics",
            "type": "Fragile", 
            "quantity": 100.0,
            "unit": "kg"
        }
        
        good_response = self.make_request('POST', 'goods', electronics_good_data)
        if not good_response or good_response.status_code != 200:
            self.log_test("Create Multi-Leg Shipment", False, error_msg="Could not create electronics good for multi-leg test")
            return False
        
        electronics_good = good_response.json()
        
        # Create multi-leg shipment: Mumbai -> Delhi -> Bangalore -> Chennai
        multi_leg_shipment_data = {
            "good": electronics_good,
            "transport_legs": [
                {
                    "from_location": {
                        "address": "Mumbai, Maharashtra, India",
                        "latitude": 19.0760,
                        "longitude": 72.8777,
                        "type": "general"
                    },
                    "to_location": {
                        "address": "New Delhi, Delhi, India", 
                        "latitude": 28.7041,
                        "longitude": 77.1025,
                        "type": "general"
                    },
                    "transport_mode": "road",
                    "vehicle_type": "Heavy Truck",
                    "cost_type": "total",
                    "cost_value": 5000.0,
                    "manual_distance": None
                },
                {
                    "from_location": {
                        "address": "New Delhi, Delhi, India",
                        "latitude": 28.7041,
                        "longitude": 77.1025,
                        "type": "general"
                    },
                    "to_location": {
                        "address": "Bangalore, Karnataka, India",
                        "latitude": 12.9716,
                        "longitude": 77.5946,
                        "type": "general"
                    },
                    "transport_mode": "rail",
                    "vehicle_type": "Freight Train",
                    "cost_type": "total",
                    "cost_value": 3000.0,
                    "manual_distance": None
                },
                {
                    "from_location": {
                        "address": "Bangalore, Karnataka, India",
                        "latitude": 12.9716,
                        "longitude": 77.5946,
                        "type": "general"
                    },
                    "to_location": {
                        "address": "Chennai, Tamil Nadu, India",
                        "latitude": 13.0827,
                        "longitude": 80.2707,
                        "type": "general"
                    },
                    "transport_mode": "air",
                    "vehicle_type": "Cargo Flight",
                    "cost_type": "total",
                    "cost_value": 8000.0,
                    "manual_distance": None
                }
            ]
        }
        
        response = self.make_request('POST', 'shipments', multi_leg_shipment_data)
        if response and response.status_code == 200:
            shipment = response.json()
            
            # Validate multi-leg shipment structure
            if len(shipment['transport_legs']) != 3:
                self.log_test("Create Multi-Leg Shipment", False, error_msg=f"Expected 3 legs, got {len(shipment['transport_legs'])}")
                return False
            
            # Validate each leg has calculated distance
            total_expected_distance = 0
            total_expected_cost = 5000 + 3000 + 8000  # 16000
            
            for i, leg in enumerate(shipment['transport_legs']):
                if leg['distance_km'] <= 0:
                    self.log_test("Create Multi-Leg Shipment", False, error_msg=f"Leg {i+1} has invalid distance: {leg['distance_km']}")
                    return False
                total_expected_distance += leg['distance_km']
            
            # Validate total calculations
            if abs(shipment['total_cost'] - total_expected_cost) > 0.01:
                self.log_test("Create Multi-Leg Shipment", False, error_msg=f"Total cost mismatch. Expected: {total_expected_cost}, Got: {shipment['total_cost']}")
                return False
            
            if abs(shipment['total_distance'] - total_expected_distance) > 0.01:
                self.log_test("Create Multi-Leg Shipment", False, error_msg=f"Total distance mismatch. Expected: {total_expected_distance}, Got: {shipment['total_distance']}")
                return False
            
            # Validate emissions calculation
            if shipment['total_emissions'] <= 0:
                self.log_test("Create Multi-Leg Shipment", False, error_msg=f"Total emissions should be > 0, got: {shipment['total_emissions']}")
                return False
            
            self.created_shipment_id = shipment['id']
            details = f"Created 3-leg shipment: Distance={shipment['total_distance']:.2f}km, Cost=₹{shipment['total_cost']:.2f}, Emissions={shipment['total_emissions']:.2f}kg CO₂"
            self.log_test("Create Multi-Leg Shipment", True, details)
            return True
        else:
            error_msg = f"Failed to create multi-leg shipment - Status: {response.status_code if response else 'No response'}"
            if response:
                error_msg += f" - Response: {response.text}"
            self.log_test("Create Multi-Leg Shipment", False, error_msg=error_msg)
            return False

    def test_multi_leg_variations(self):
        """Test different multi-leg shipment variations (2, 4, 5 legs)"""
        # Create a test good
        test_good_data = {
            "name": "Test Cargo",
            "type": "General",
            "quantity": 50.0,
            "unit": "kg"
        }
        
        good_response = self.make_request('POST', 'goods', test_good_data)
        if not good_response or good_response.status_code != 200:
            self.log_test("Multi-Leg Variations", False, error_msg="Could not create test good")
            return False
        
        test_good = good_response.json()
        
        # Test 2-leg shipment
        two_leg_data = {
            "good": test_good,
            "transport_legs": [
                {
                    "from_location": {
                        "address": "Mumbai, Maharashtra, India",
                        "latitude": 19.0760,
                        "longitude": 72.8777,
                        "type": "general"
                    },
                    "to_location": {
                        "address": "Pune, Maharashtra, India",
                        "latitude": 18.5204,
                        "longitude": 73.8567,
                        "type": "general"
                    },
                    "transport_mode": "road",
                    "vehicle_type": "Heavy Truck",
                    "cost_type": "total",
                    "cost_value": 2000.0
                },
                {
                    "from_location": {
                        "address": "Pune, Maharashtra, India",
                        "latitude": 18.5204,
                        "longitude": 73.8567,
                        "type": "general"
                    },
                    "to_location": {
                        "address": "Bangalore, Karnataka, India",
                        "latitude": 12.9716,
                        "longitude": 77.5946,
                        "type": "general"
                    },
                    "transport_mode": "rail",
                    "vehicle_type": "Freight Train",
                    "cost_type": "total",
                    "cost_value": 4000.0
                }
            ]
        }
        
        response = self.make_request('POST', 'shipments', two_leg_data)
        if response and response.status_code == 200:
            shipment = response.json()
            if len(shipment['transport_legs']) == 2 and shipment['total_cost'] == 6000.0:
                self.log_test("2-Leg Shipment", True, f"Distance: {shipment['total_distance']:.2f}km, Cost: ₹{shipment['total_cost']}")
            else:
                self.log_test("2-Leg Shipment", False, error_msg="Invalid 2-leg shipment structure")
                return False
        else:
            self.log_test("2-Leg Shipment", False, error_msg="Failed to create 2-leg shipment")
            return False
        
        # Test 5-leg shipment (maximum allowed)
        five_leg_data = {
            "good": test_good,
            "transport_legs": [
                {
                    "from_location": {"address": "Mumbai, India", "latitude": 19.0760, "longitude": 72.8777, "type": "general"},
                    "to_location": {"address": "Pune, India", "latitude": 18.5204, "longitude": 73.8567, "type": "general"},
                    "transport_mode": "road", "vehicle_type": "Heavy Truck", "cost_type": "total", "cost_value": 1000.0
                },
                {
                    "from_location": {"address": "Pune, India", "latitude": 18.5204, "longitude": 73.8567, "type": "general"},
                    "to_location": {"address": "Hyderabad, India", "latitude": 17.3850, "longitude": 78.4867, "type": "general"},
                    "transport_mode": "rail", "vehicle_type": "Freight Train", "cost_type": "total", "cost_value": 2000.0
                },
                {
                    "from_location": {"address": "Hyderabad, India", "latitude": 17.3850, "longitude": 78.4867, "type": "general"},
                    "to_location": {"address": "Bangalore, India", "latitude": 12.9716, "longitude": 77.5946, "type": "general"},
                    "transport_mode": "road", "vehicle_type": "Heavy Truck", "cost_type": "total", "cost_value": 1500.0
                },
                {
                    "from_location": {"address": "Bangalore, India", "latitude": 12.9716, "longitude": 77.5946, "type": "general"},
                    "to_location": {"address": "Chennai, India", "latitude": 13.0827, "longitude": 80.2707, "type": "general"},
                    "transport_mode": "air", "vehicle_type": "Cargo Flight", "cost_type": "total", "cost_value": 5000.0
                },
                {
                    "from_location": {"address": "Chennai, India", "latitude": 13.0827, "longitude": 80.2707, "type": "general"},
                    "to_location": {"address": "Kolkata, India", "latitude": 22.5726, "longitude": 88.3639, "type": "general"},
                    "transport_mode": "rail", "vehicle_type": "Freight Train", "cost_type": "total", "cost_value": 3000.0
                }
            ]
        }
        
        response = self.make_request('POST', 'shipments', five_leg_data)
        if response and response.status_code == 200:
            shipment = response.json()
            if len(shipment['transport_legs']) == 5 and shipment['total_cost'] == 12500.0:
                self.log_test("5-Leg Shipment", True, f"Distance: {shipment['total_distance']:.2f}km, Cost: ₹{shipment['total_cost']}")
                return True
            else:
                self.log_test("5-Leg Shipment", False, error_msg="Invalid 5-leg shipment structure")
                return False
        else:
            self.log_test("5-Leg Shipment", False, error_msg="Failed to create 5-leg shipment")
            return False

    def test_get_shipments(self):
        """Test getting shipments"""
        response = self.make_request('GET', 'shipments')
        if response and response.status_code == 200:
            shipments = response.json()
            self.log_test("Get Shipments", True, f"Found {len(shipments)} shipments")
            return True
        else:
            error_msg = f"Failed to get shipments - Status: {response.status_code if response else 'No response'}"
            self.log_test("Get Shipments", False, error_msg=error_msg)
            return False

    def test_emission_factor_crud(self):
        """Test CRUD operations for emission factors"""
        # Create new emission factor
        factor_data = {
            "transport_mode": "road",
            "vehicle_type": "Test Vehicle",
            "emission_factor": 0.25,
            "unit": "kgCO2/tonne-km"
        }
        
        response = self.make_request('POST', 'emission-factors', factor_data)
        if response and response.status_code == 200:
            created_factor = response.json()
            factor_id = created_factor['id']
            self.log_test("Create Emission Factor", True, f"Created factor with ID: {factor_id}")
            
            # Update the emission factor
            updated_data = {
                "transport_mode": "road",
                "vehicle_type": "Test Vehicle Updated",
                "emission_factor": 0.30,
                "unit": "kgCO2/tonne-km"
            }
            
            update_response = self.make_request('PUT', f'emission-factors/{factor_id}', updated_data)
            if update_response and update_response.status_code == 200:
                self.log_test("Update Emission Factor", True, "Successfully updated emission factor")
                
                # Delete the emission factor
                delete_response = self.make_request('DELETE', f'emission-factors/{factor_id}')
                if delete_response and delete_response.status_code == 200:
                    self.log_test("Delete Emission Factor", True, "Successfully deleted emission factor")
                    return True
                else:
                    error_msg = f"Failed to delete emission factor - Status: {delete_response.status_code if delete_response else 'No response'}"
                    self.log_test("Delete Emission Factor", False, error_msg=error_msg)
                    return False
            else:
                error_msg = f"Failed to update emission factor - Status: {update_response.status_code if update_response else 'No response'}"
                self.log_test("Update Emission Factor", False, error_msg=error_msg)
                return False
        else:
            error_msg = f"Failed to create emission factor - Status: {response.status_code if response else 'No response'}"
            self.log_test("Create Emission Factor", False, error_msg=error_msg)
            return False

    def test_dashboard_data_storage(self):
        """Test that multi-leg shipments are properly stored and retrievable for dashboard"""
        # Get all shipments to verify storage
        response = self.make_request('GET', 'shipments')
        if not response or response.status_code != 200:
            self.log_test("Dashboard Data Storage", False, error_msg="Could not retrieve shipments for dashboard test")
            return False
        
        shipments = response.json()
        
        # Find multi-leg shipments
        multi_leg_shipments = [s for s in shipments if len(s.get('transport_legs', [])) > 1]
        
        if len(multi_leg_shipments) == 0:
            self.log_test("Dashboard Data Storage", False, error_msg="No multi-leg shipments found in storage")
            return False
        
        # Verify structure of stored multi-leg shipments
        for shipment in multi_leg_shipments[:3]:  # Check first 3 multi-leg shipments
            # Verify required fields exist
            required_fields = ['id', 'good', 'transport_legs', 'total_distance', 'total_cost', 'total_emissions', 'created_at']
            for field in required_fields:
                if field not in shipment:
                    self.log_test("Dashboard Data Storage", False, error_msg=f"Missing field '{field}' in stored shipment")
                    return False
            
            # Verify each transport leg has required fields
            for i, leg in enumerate(shipment['transport_legs']):
                leg_required_fields = ['id', 'from_location', 'to_location', 'transport_mode', 'vehicle_type', 'distance_km', 'cost_value']
                for field in leg_required_fields:
                    if field not in leg:
                        self.log_test("Dashboard Data Storage", False, error_msg=f"Missing field '{field}' in leg {i+1} of stored shipment")
                        return False
        
        self.log_test("Dashboard Data Storage", True, f"Found {len(multi_leg_shipments)} properly stored multi-leg shipments")
        return True

    def test_analytics_with_multi_leg_data(self):
        """Test analytics endpoint with multi-leg shipment data"""
        analytics_data = {"time_period": "30days"}
        
        response = self.make_request('POST', 'shipments/analytics', analytics_data)
        if response and response.status_code == 200:
            analytics = response.json()
            
            # Verify analytics structure
            required_fields = ['total_shipments', 'total_cost', 'total_emissions', 'total_distance', 'goods_breakdown']
            for field in required_fields:
                if field not in analytics:
                    self.log_test("Analytics with Multi-Leg Data", False, error_msg=f"Missing field '{field}' in analytics")
                    return False
            
            # Verify analytics has data (should include our multi-leg shipments)
            if analytics['total_shipments'] > 0:
                details = f"Shipments: {analytics['total_shipments']}, Total Cost: ₹{analytics['total_cost']}, Total Emissions: {analytics['total_emissions']}kg CO₂"
                self.log_test("Analytics with Multi-Leg Data", True, details)
                return True
            else:
                self.log_test("Analytics with Multi-Leg Data", False, error_msg="Analytics shows 0 shipments")
                return False
        else:
            error_msg = f"Failed to get analytics - Status: {response.status_code if response else 'No response'}"
            self.log_test("Analytics with Multi-Leg Data", False, error_msg=error_msg)
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting CarbonRoute Multi-Leg Transport Backend API Tests")
        print("=" * 70)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Initialize emission factors
        self.test_initialize_emission_factors()
        
        # Test emission factors
        self.test_get_emission_factors()
        
        # Test goods CRUD
        self.test_create_good()
        self.test_get_goods()
        self.test_get_good_by_id()
        
        # Test location and search functionality
        self.test_location_search()
        
        # Test vehicle types
        self.test_vehicle_types()
        
        # Test distance calculation (general)
        self.test_distance_calculation()
        
        # Test Indian route distance calculation (specific to requirements)
        self.test_indian_route_distance_calculation()
        
        # Test single leg shipment (baseline)
        self.test_create_single_leg_shipment()
        
        # Test multi-leg shipment functionality (main requirement)
        print("\n🎯 MULTI-LEG SHIPMENT TESTING (Primary Focus)")
        print("-" * 50)
        self.test_create_multi_leg_shipment()
        self.test_multi_leg_variations()
        
        # Test shipment retrieval
        self.test_get_shipments()
        
        # Test dashboard data storage with multi-leg shipments
        self.test_dashboard_data_storage()
        
        # Test analytics with multi-leg data
        self.test_analytics_with_multi_leg_data()
        
        # Test emission factor CRUD
        self.test_emission_factor_crud()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All multi-leg transport tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

    def get_test_summary(self):
        """Get detailed test summary"""
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "test_results": self.test_results
        }

def main():
    tester = TransportEmissionAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    summary = tester.get_test_summary()
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())