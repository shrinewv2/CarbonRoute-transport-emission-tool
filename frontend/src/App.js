import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { Plus, Trash2, Calculator, Truck, Train, Plane, Ship, Package, MapPin, BarChart3, TrendingUp, Clock, X, Lightbulb, Zap } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, ScatterChart, Scatter } from 'recharts';
import { format, subDays, subMonths, subYears } from 'date-fns';
import '@/App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Color palette for charts
const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899'];

// Loading Component
const LoadingSpinner = () => (
  <div className="loading-overlay">
    <div className="spinner-container">
      <div className="spinner"></div>
      <p className="spinner-text">Calculating emissions...</p>
    </div>
  </div>
);

// Main Calculator Component
const TransportCalculator = () => {
  const [currentGood, setCurrentGood] = useState({
    name: '',
    quantity: '',
    unit: 'kg',
    ghg_category: 'upstream'
  });
  
  const [transportLegs, setTransportLegs] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [currentLeg, setCurrentLeg] = useState({
    from_location: { address: '', latitude: 0, longitude: 0, type: 'general' },
    to_location: { address: '', latitude: 0, longitude: 0, type: 'general' },
    transport_mode: '',
    vehicle_type: '',
    cost_type: 'total',
    cost_value: '',
    manual_distance: null
  });

  const [locationSearch, setLocationSearch] = useState({
    from: '',
    to: ''
  });

  const [vehicleTypes, setVehicleTypes] = useState([]);
  const [searchResults, setSearchResults] = useState({
    from: [],
    to: []
  });

  const [loading, setLoading] = useState(false);
  const [showCalculateButton, setShowCalculateButton] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState(null);
  const [calculationResult, setCalculationResult] = useState(null);
  // Transport mode icons
  const transportIcons = {
    road: Truck,
    rail: Train,
    air: Plane,
    water: Ship
  };

  const transportModes = [
    { value: 'road', label: 'Road Transport' },
    { value: 'rail', label: 'Railway' },
    { value: 'air', label: 'Airways' },
    { value: 'water', label: 'Seaways' }
  ];

  // Initialize emission factors on app load
  useEffect(() => {
    const initializeApp = async () => {
      try {
        await axios.post(`${API}/init-emission-factors`);
        await loadShipments();
      } catch (error) {
        console.error('App initialization error:', error);
      }
    };
    initializeApp();
  }, []);

  // Check if calculate button should be shown
  useEffect(() => {
    setShowCalculateButton(
      currentGood.name && 
      currentGood.quantity && 
      currentGood.ghg_category && 
      transportLegs.length > 0
    );
  }, [currentGood, transportLegs]);

  const loadShipments = async () => {
    try {
      const response = await axios.get(`${API}/shipments`);
      setShipments(response.data);
    } catch (error) {
      console.error('Error loading shipments:', error);
    }
  };

  const searchLocations = async (query, locationType = 'general') => {
    if (query.length < 1) return [];
    
    try {
      const endpoint = locationType === 'airport' 
        ? `${API}/airports/search?query=${encodeURIComponent(query)}`
        : `${API}/locations/search?query=${encodeURIComponent(query)}&location_type=${locationType}`;
      
      const response = await axios.get(endpoint);
      
      if (locationType === 'airport') {
        return response.data.slice(0, 6).map(airport => ({
          address: `${airport.name} (${airport.code}) - ${airport.city}, ${airport.country}`,
          latitude: airport.latitude,
          longitude: airport.longitude,
          type: 'airport'
        }));
      }
      
      return response.data.slice(0, 6);
    } catch (error) {
      console.error('Location search error:', error);
      return [];
    }
  };

  const handleLocationSearch = async (field, query) => {
    setLocationSearch(prev => ({ ...prev, [field]: query }));
    
    // Clear existing timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    if (query.length >= 1) {
      // Debounce search with 300ms delay
      const newTimeout = setTimeout(async () => {
        const locationType = currentLeg.transport_mode === 'air' ? 'airport' : 'general';
        try {
          console.log(`Searching for: ${query} (type: ${locationType})`);
          const results = await searchLocations(query, locationType);
          console.log(`Search results:`, results);
          setSearchResults(prev => ({ 
            ...prev, 
            [field]: Array.isArray(results) ? results : [] 
          }));
        } catch (error) {
          console.error('Search error:', error);
          setSearchResults(prev => ({ ...prev, [field]: [] }));
        }
      }, 300);
      
      setSearchTimeout(newTimeout);
    } else {
      setSearchResults(prev => ({ ...prev, [field]: [] }));
    }
  };

  const selectLocation = (field, location) => {
    setCurrentLeg(prev => ({
      ...prev,
      [`${field}_location`]: location
    }));
    setLocationSearch(prev => ({ ...prev, [field]: location.address }));
    setSearchResults(prev => ({ ...prev, [field]: [] }));
  };

  const loadVehicleTypes = async (transportMode) => {
    try {
      const response = await axios.get(`${API}/vehicle-types/${transportMode}`);
      setVehicleTypes(response.data.vehicle_types);
    } catch (error) {
      console.error('Error loading vehicle types:', error);
      setVehicleTypes([]);
    }
  };

  useEffect(() => {
    if (currentLeg.transport_mode) {
      loadVehicleTypes(currentLeg.transport_mode);
    } else {
      setVehicleTypes([]); // Clear vehicle types when no transport mode selected
    }
  }, [currentLeg.transport_mode]);

  const handleGoodChange = (field, value) => {
    setCurrentGood(prev => ({ ...prev, [field]: value }));
  };

  const handleLegChange = (field, value) => {
    setCurrentLeg(prev => ({ ...prev, [field]: value }));
  };

  const addTransportLeg = async () => {
    // Check maximum legs limit
    if (transportLegs.length >= 5) {
      toast.error('Maximum 5 transport legs allowed');
      return;
    }

    if (!currentLeg.from_location.address || !currentLeg.to_location.address || 
        !currentLeg.transport_mode || !currentLeg.vehicle_type || !currentLeg.cost_value) {
      toast.error('Please fill in all required fields for the transport leg');
      return;
    }

    setLoading(true);
    try {
      // Calculate distance
      let distance = null;
      if (currentLeg.manual_distance) {
        distance = parseFloat(currentLeg.manual_distance);
      } else {
        const distanceResponse = await axios.post(`${API}/calculate-distance`, {
          from_location: currentLeg.from_location,
          to_location: currentLeg.to_location,
          transport_mode: currentLeg.transport_mode
        });
        distance = distanceResponse.data.distance_km;
      }

      const newLeg = {
        ...currentLeg,
        distance_km: distance,
        cost_value: parseFloat(currentLeg.cost_value)
      };

      setTransportLegs(prev => [...prev, newLeg]);
      
      // Reset current leg and clear related states
      setCurrentLeg({
        from_location: { address: '', latitude: 0, longitude: 0, type: 'general' },
        to_location: { address: '', latitude: 0, longitude: 0, type: 'general' },
        transport_mode: '',
        vehicle_type: '',
        cost_type: 'total',
        cost_value: '',
        manual_distance: null
      });
      setLocationSearch({ from: '', to: '' });
      setVehicleTypes([]); // Clear vehicle types when resetting
      setSearchResults({ from: [], to: [] }); // Clear search results
      
      toast.success(`Transport leg added successfully (${transportLegs.length + 1}/5)`);
    } catch (error) {
      console.error('Error adding transport leg:', error);
      toast.error('Error adding transport leg');
    } finally {
      setLoading(false);
    }
  };

  const removeTransportLeg = (index) => {
    setTransportLegs(prev => prev.filter((_, i) => i !== index));
  };

  const calculateShipment = async () => {
    if (!currentGood.name || !currentGood.quantity || !currentGood.ghg_category || transportLegs.length === 0) {
      toast.error('Please add good details and at least one transport leg');
      return;
    }

    setLoading(true);
    try {
      const shipmentData = {
        good: {
          ...currentGood,
          quantity: parseFloat(currentGood.quantity)
        },
        transport_legs: transportLegs
      };

      const response = await axios.post(`${API}/shipments`, shipmentData);
      const shipment = response.data;
      
      // Store calculation result to display
      setCalculationResult(shipment);
      await loadShipments();
      
      toast.success('Shipment calculated successfully!');
    } catch (error) {
      console.error('Error calculating shipment:', error);
      toast.error('Error calculating shipment');
    } finally {
      setLoading(false);
    }
  };

  const resetCalculation = () => {
    setCurrentGood({ name: '', quantity: '', unit: 'kg', ghg_category: 'upstream' });
    setTransportLegs([]);
    setLocationSearch({ from: '', to: '' });
    setCalculationResult(null);
    setVehicleTypes([]);
    setSearchResults({ from: [], to: [] });
    setCurrentLeg({
      from_location: { address: '', latitude: 0, longitude: 0, type: 'general' },
      to_location: { address: '', latitude: 0, longitude: 0, type: 'general' },
      transport_mode: '',
      vehicle_type: '',
      cost_type: 'total',
      cost_value: '',
      manual_distance: null
    });
  };

  // Removed AI optimization features

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {loading && <LoadingSpinner />}
      <div className="container mx-auto py-8 px-4">
        <div className="text-center mb-8">
          <div className="flex justify-between items-center mb-6">
            <div className="logo-container flex items-center gap-3">
              <img
                src="/assets/Arantree_logo_upscaled.png"
                alt="Arantree Consulting Services"
                className="logo-img h-12 w-auto"
                onError={(e) => { e.target.style.display = 'none' }}
              />
              <div className="text-left">
                <p className="text-xs text-slate-500 font-medium">Powered by</p>
                <p className="text-sm font-semibold text-slate-700">Arantree Consulting Services</p>
              </div>
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent animate-float">
              CarbonRoute
            </h1>
            <a href="/admin" className="text-sm text-blue-600 hover:text-blue-700 transition-all duration-300 font-semibold hover:scale-105" data-testid="admin-link">
              Admin Panel →
            </a>
          </div>
          <p className="text-lg text-slate-600 max-w-3xl mx-auto leading-relaxed">
            Transportation emission calculator according to Scope 3 emissions - Transportation categories
          </p>
        </div>

        <Tabs defaultValue="calculator" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-md mx-auto bg-white/80 border border-slate-200 backdrop-blur-sm">
            <TabsTrigger value="calculator" data-testid="calculator-tab" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white text-slate-700">Calculator</TabsTrigger>
            <TabsTrigger value="dashboard" data-testid="dashboard-tab" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white text-slate-700">Dashboard</TabsTrigger>
          </TabsList>

          <TabsContent value="calculator" className="space-y-6">
            {/* Goods Section */}
            <Card data-testid="goods-section" className="bg-white/70 border-slate-200 backdrop-blur-sm shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-700">
                  <Package className="h-5 w-5" />
                  Goods Information
                </CardTitle>
                <CardDescription className="text-slate-600">
                  Enter details about the goods you want to transport
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <Label htmlFor="good-name" className="text-slate-700">Good Name</Label>
                    <Input
                      id="good-name"
                      value={currentGood.name}
                      onChange={(e) => handleGoodChange('name', e.target.value)}
                      placeholder="e.g., Electronics, Textiles"
                      data-testid="good-name-input"
                      className="bg-white/80 border-slate-300 text-slate-800 placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <Label htmlFor="quantity" className="text-slate-700">Quantity</Label>
                    <Input
                      id="quantity"
                      type="number"
                      value={currentGood.quantity}
                      onChange={(e) => handleGoodChange('quantity', e.target.value)}
                      placeholder="Enter quantity"
                      data-testid="good-quantity-input"
                      className="bg-white/80 border-slate-300 text-slate-800 placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <Label htmlFor="unit" className="text-slate-700">Unit</Label>
                    <Select value={currentGood.unit} onValueChange={(value) => handleGoodChange('unit', value)}>
                      <SelectTrigger data-testid="good-unit-select" className="bg-white/80 border-slate-300 text-slate-800">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-white border-slate-200">
                        <SelectItem value="kg">Kilograms (kg)</SelectItem>
                        <SelectItem value="tons">Tonnes</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="ghg-category" className="text-slate-700">GHG Category</Label>
                    <Select value={currentGood.ghg_category} onValueChange={(value) => handleGoodChange('ghg_category', value)}>
                      <SelectTrigger data-testid="good-ghg-category-select" className="bg-white/80 border-slate-300 text-slate-800">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-white border-slate-200">
                        <SelectItem value="upstream">Upstream Transportation</SelectItem>
                        <SelectItem value="downstream">Downstream Transportation</SelectItem>
                        <SelectItem value="company_owned">Company Owned Transportation</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Transport Leg Section */}
            <Card data-testid="transport-leg-section" className="bg-white/70 border-slate-200 backdrop-blur-sm shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-700">
                  <MapPin className="h-5 w-5" />
                  Add Transport Leg
                </CardTitle>
                <CardDescription className="text-slate-600">
                  Add transportation segments for your goods
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Transport Mode Selection */}
                <div>
                  <Label className="text-slate-700">Transport Mode</Label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
                    {transportModes.map((mode) => {
                      const Icon = transportIcons[mode.value];
                      return (
                        <Card 
                          key={mode.value}
                          className={`cursor-pointer transition-all duration-300 hover:shadow-lg ${
                            currentLeg.transport_mode === mode.value 
                              ? 'ring-2 ring-blue-500 bg-blue-50 border-blue-300' 
                              : 'bg-white/80 border-slate-200 hover:border-blue-300'
                          }`}
                          onClick={() => handleLegChange('transport_mode', mode.value)}
                          data-testid={`transport-mode-${mode.value}`}
                        >
                          <CardContent className="flex flex-col items-center p-4">
                            <Icon className="h-8 w-8 mb-2 text-blue-600" />
                            <span className="text-sm font-medium text-center text-slate-700">{mode.label}</span>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                </div>

                {/* Location Selection */}
                {currentLeg.transport_mode && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="relative location-input-container">
                      <Label htmlFor="from-location" className="text-slate-700">From Location</Label>
                      <Input
                        id="from-location"
                        value={locationSearch.from}
                        onChange={(e) => handleLocationSearch('from', e.target.value)}
                        placeholder={currentLeg.transport_mode === 'air' ? 'Search airports...' : 'Search locations...'}
                        data-testid="from-location-input"
                        className="bg-white/80 border-slate-300 text-slate-800 placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500"
                      />
                      {searchResults.from.length > 0 && (
                        <div className="search-dropdown location-dropdown-visible">
                          {searchResults.from.map((location, index) => (
                            <div
                              key={index}
                              className="search-option"
                              onClick={() => selectLocation('from', location)}
                              data-testid={`from-location-option-${index}`}
                            >
                              <div className="font-medium text-sm">{location.address}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="relative location-input-container">
                      <Label htmlFor="to-location" className="text-slate-700">To Location</Label>
                      <Input
                        id="to-location"
                        value={locationSearch.to}
                        onChange={(e) => handleLocationSearch('to', e.target.value)}
                        placeholder={currentLeg.transport_mode === 'air' ? 'Search airports...' : 'Search locations...'}
                        data-testid="to-location-input"
                        className="bg-white/80 border-slate-300 text-slate-800 placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500"
                      />
                      {searchResults.to.length > 0 && (
                        <div className="search-dropdown location-dropdown-visible">
                          {searchResults.to.map((location, index) => (
                            <div
                              key={index}
                              className="search-option"
                              onClick={() => selectLocation('to', location)}
                              data-testid={`to-location-option-${index}`}
                            >
                              <div className="font-medium text-sm">{location.address}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Vehicle Type and Cost */}
                {currentLeg.transport_mode && currentLeg.from_location.address && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="vehicle-type" className="text-slate-700">Vehicle Type</Label>
                      <Select 
                        value={currentLeg.vehicle_type} 
                        onValueChange={(value) => handleLegChange('vehicle_type', value)}
                      >
                        <SelectTrigger data-testid="vehicle-type-select" className="bg-white/80 border-slate-300 text-slate-800">
                          <SelectValue placeholder="Select vehicle type" />
                        </SelectTrigger>
                        <SelectContent className="bg-white border-slate-200">
                          {vehicleTypes.map((type) => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="cost-type" className="text-slate-700">Cost Type</Label>
                      <Select 
                        value={currentLeg.cost_type} 
                        onValueChange={(value) => handleLegChange('cost_type', value)}
                      >
                        <SelectTrigger data-testid="cost-type-select" className="bg-white/80 border-slate-300 text-slate-800">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-white border-slate-200">
                          <SelectItem value="total">Total Cost</SelectItem>
                          <SelectItem value="per_kg">Cost per KG</SelectItem>
                          <SelectItem value="per_ton">Cost per Tonne</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="cost-value" className="text-slate-700">Cost Value</Label>
                      <Input
                        id="cost-value"
                        type="number"
                        value={currentLeg.cost_value}
                        onChange={(e) => handleLegChange('cost_value', e.target.value)}
                        placeholder="Enter cost"
                        data-testid="cost-value-input"
                        className="bg-white/80 border-slate-300 text-slate-800 placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}

                {/* Manual Distance Option */}
                {currentLeg.transport_mode && (
                  <div>
                    <Label htmlFor="manual-distance" className="text-slate-700">Manual Distance (km) - Optional</Label>
                    <Input
                      id="manual-distance"
                      type="number"
                      value={currentLeg.manual_distance || ''}
                      onChange={(e) => handleLegChange('manual_distance', e.target.value || null)}
                      placeholder="Enter distance manually (optional)"
                      data-testid="manual-distance-input"
                      className="bg-white/80 border-slate-300 text-slate-800 placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                )}

                <Button
                  onClick={addTransportLeg}
                  disabled={loading || transportLegs.length >= 5}
                  className="w-full bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 btn-enhanced disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                  data-testid="add-transport-leg-btn"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Transport Leg {transportLegs.length > 0 && `(${transportLegs.length}/5)`}
                </Button>
              </CardContent>
            </Card>

            {/* Current Transport Legs */}
            {transportLegs.length > 0 && (
              <Card data-testid="current-legs-section" className="bg-white/70 border-slate-200 backdrop-blur-sm shadow-lg">
                <CardHeader>
                  <CardTitle className="text-blue-700">Transport Legs</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {transportLegs.map((leg, index) => {
                    const Icon = transportIcons[leg.transport_mode];
                    return (
                      <div key={index} className="flex items-center justify-between p-4 bg-slate-50/80 rounded-lg border border-slate-200">
                        <div className="flex items-center gap-3">
                          <Icon className="h-5 w-5 text-blue-600" />
                          <div>
                            <div className="font-medium text-slate-800">
                              {leg.from_location.address} → {leg.to_location.address}
                            </div>
                            <div className="text-sm text-slate-600">
                              {leg.vehicle_type} • {leg.distance_km?.toFixed(2)} km • 
                              {leg.cost_type === 'total' ? `₹${leg.cost_value}` : 
                               `₹${leg.cost_value}/${leg.cost_type.replace('per_', '')}`}
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeTransportLeg(index)}
                          data-testid={`remove-leg-${index}`}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            )}

            {/* Calculation Result Display */}
            {calculationResult && (
              <Card data-testid="calculation-result" className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 backdrop-blur-sm shadow-lg">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-green-700">
                    <Calculator className="h-5 w-5" />
                    Calculation Results
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={resetCalculation}
                    className="text-slate-600 hover:text-slate-800 hover:bg-red-50"
                    data-testid="reset-calculation-btn"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                    <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="text-3xl font-bold text-blue-600 mb-2">
                        {calculationResult.total_distance?.toFixed(1)} km
                      </div>
                      <div className="text-sm text-slate-600">Total Distance</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
                      <div className="text-3xl font-bold text-green-600 mb-2">
                        ₹{calculationResult.total_cost?.toLocaleString()}
                      </div>
                      <div className="text-sm text-slate-600">Total Cost</div>
                    </div>
                    <div className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <div className="text-3xl font-bold text-orange-600 mb-2">
                        {calculationResult.total_emissions?.toFixed(2)} kg
                      </div>
                      <div className="text-sm text-slate-600">CO₂ Emissions</div>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
                      <div className="text-3xl font-bold text-purple-600 mb-2">
                        {calculationResult.good?.quantity} {calculationResult.good?.unit}
                      </div>
                      <div className="text-sm text-slate-600">Total Weight</div>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-semibold text-slate-800 mb-3">Transport Legs Summary:</h4>
                    {calculationResult.transport_legs?.map((leg, index) => {
                      const Icon = transportIcons[leg.transport_mode];
                      return (
                        <div key={index} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                          <Icon className="h-5 w-5 text-blue-600" />
                          <div className="flex-1">
                            <div className="text-slate-800 font-medium">
                              {leg.from_location.address} → {leg.to_location.address}
                            </div>
                            <div className="text-slate-600 text-sm">
                              {leg.vehicle_type} • {leg.distance_km?.toFixed(1)} km • 
                              {leg.cost_type === 'total' ? `₹${leg.cost_value}` : 
                               `₹${leg.cost_value}/${leg.cost_type.replace('per_', '')}`}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  <div className="mt-6">
                    <Button 
                      onClick={resetCalculation}
                      variant="outline"
                      className="w-full border-slate-300 text-slate-700 hover:bg-slate-50 hover:text-slate-800"
                      data-testid="start-new-calculation-btn"
                    >
                      Start New Calculation
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Removed AI Optimization Suggestions */}

            {/* Calculate and Add More Buttons */}
            {showCalculateButton && !calculationResult && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card data-testid="calculate-section" className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
                  <CardContent className="p-6">
                    <Button
                      onClick={calculateShipment}
                      disabled={loading}
                      className="w-full h-12 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 btn-enhanced shadow-lg"
                      data-testid="calculate-shipment-btn"
                    >
                      <Calculator className="h-5 w-5 mr-2" />
                      Calculate Emissions & Cost
                    </Button>
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200">
                  <CardContent className="p-6">
                    <Button 
                      onClick={() => {
                        // Reset form for next leg while keeping goods info
                        setCurrentLeg({
                          from_location: { address: '', latitude: 0, longitude: 0, type: 'general' },
                          to_location: { address: '', latitude: 0, longitude: 0, type: 'general' },
                          transport_mode: '',
                          vehicle_type: '',
                          cost_type: 'total',
                          cost_value: '',
                          manual_distance: null
                        });
                        setLocationSearch({ from: '', to: '' });
                      }}
                      className="w-full h-12 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 transition-all duration-300"
                      data-testid="add-more-leg-btn"
                    >
                      <Plus className="h-5 w-5 mr-2" />
                      Add Another Transport Leg
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          <TabsContent value="dashboard" className="space-y-6">
            <DashboardContent shipments={shipments} onShipmentsChange={loadShipments} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// Custom scatter shape with size based on quantity
const CustomScatterShape = (props) => {
  const { cx, cy, fill, payload } = props;
  // Scale bubble size based on quantity (z value)
  // Min size: 6, Max size: 20, based on quantity
  const baseSize = 8;
  const scaleFactor = Math.min(Math.max(payload.z / 100, 0.5), 3); // Scale factor between 0.5 and 3
  const radius = baseSize * scaleFactor;

  return (
    <circle
      cx={cx}
      cy={cy}
      r={radius}
      fill={fill}
      fillOpacity={0.7}
      stroke={fill}
      strokeWidth={2}
      strokeOpacity={1}
    />
  );
};

// Dashboard Component with Charts and Analytics
const DashboardContent = ({ shipments, onShipmentsChange }) => {
  const [loading, setLoading] = useState(false);
  const [selectedShipments, setSelectedShipments] = useState([]);
  const [scatterData, setScatterData] = useState(null);
  const [categoryFilters, setCategoryFilters] = useState({
    upstream: true,
    downstream: true,
    company_owned: true
  });

  // Load scatter plot data
  useEffect(() => {
    const loadScatterData = async () => {
      try {
        const response = await axios.get(`${API}/shipments/scatter-analytics`);
        setScatterData(response.data);
      } catch (error) {
        console.error('Error loading scatter data:', error);
      }
    };
    
    if (shipments.length > 0) {
      loadScatterData();
    }
  }, [shipments]);

  const handleSelectShipment = (shipmentId, checked) => {
    setSelectedShipments(prev => {
      if (checked) {
        return [...prev, shipmentId];
      } else {
        return prev.filter(id => id !== shipmentId);
      }
    });
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedShipments(shipments.map(s => s.id));
    } else {
      setSelectedShipments([]);
    }
  };

  const toggleCategoryFilter = (category) => {
    setCategoryFilters(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  const handleBulkDelete = async () => {
    if (selectedShipments.length === 0) {
      toast.error('Please select shipments to delete');
      return;
    }

    try {
      setLoading(true);
      await axios.delete(`${API}/shipments/bulk`, {
        data: { shipment_ids: selectedShipments }
      });
      
      toast.success(`Successfully deleted ${selectedShipments.length} shipments`);
      setSelectedShipments([]);
      onShipmentsChange(); // Refresh shipments list
    } catch (error) {
      console.error('Error deleting shipments:', error);
      toast.error('Error deleting shipments');
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = () => {
    if (!shipments || shipments.length === 0) return [];
    
    // Group by goods for charts
    const goodsData = {};
    shipments.forEach((shipment) => {
      const goodName = shipment.good?.name || 'Unknown';
      if (!goodsData[goodName]) {
        goodsData[goodName] = {
          name: goodName,
          cost: 0,
          emissions: 0,
          distance: 0,
          count: 0
        };
      }
      
      goodsData[goodName].cost += shipment.total_cost || 0;
      goodsData[goodName].emissions += shipment.total_emissions || 0;
      goodsData[goodName].distance += shipment.total_distance || 0;
      goodsData[goodName].count += 1;
    });
    
    return Object.values(goodsData).map((item, index) => ({
      name: item.name,
      cost: Math.round(item.cost),
      emissions: Math.round(item.emissions * 100) / 100,
      distance: Math.round(item.distance),
      count: item.count,
      fill: CHART_COLORS[index % CHART_COLORS.length]
    }));
  };

  const calculateTotals = () => {
    return {
      totalShipments: shipments.length,
      totalCost: shipments.reduce((sum, s) => sum + (s.total_cost || 0), 0),
      totalEmissions: shipments.reduce((sum, s) => sum + (s.total_emissions || 0), 0),
      upstreamEmissions: shipments.reduce((sum, s) => sum + (s.upstream_emissions || 0), 0),
      downstreamEmissions: shipments.reduce((sum, s) => sum + (s.downstream_emissions || 0), 0),
      companyOwnedEmissions: shipments.reduce((sum, s) => sum + (s.company_owned_emissions || 0), 0),
      totalDistance: shipments.reduce((sum, s) => sum + (s.total_distance || 0), 0)
    };
  };

  const prepareScatterData = () => {
    if (!scatterData) return { upstream: [], downstream: [], company_owned: [] };
    
    return {
      upstream: scatterData.upstream.map(item => ({
        x: item.emissions,
        y: item.cost,
        z: item.quantity,
        name: item.good_name
      })),
      downstream: scatterData.downstream.map(item => ({
        x: item.emissions,
        y: item.cost,
        z: item.quantity,
        name: item.good_name
      })),
      company_owned: scatterData.company_owned.map(item => ({
        x: item.emissions,
        y: item.cost,
        z: item.quantity,
        name: item.good_name
      }))
    };
  };

  const totals = calculateTotals();
  const scatterPlotData = prepareScatterData();

  return (
    <div className="space-y-6">
      {/* Analytics Summary Cards - 4 Totals */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200">
          <CardContent className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600 mb-2">
                {totals.upstreamEmissions.toFixed(1)} kg CO₂
              </div>
              <div className="text-sm text-slate-600">Upstream Emissions</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <CardContent className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 mb-2">
                {totals.downstreamEmissions.toFixed(1)} kg CO₂
              </div>
              <div className="text-sm text-slate-600">Downstream Emissions</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
          <CardContent className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600 mb-2">
                {totals.companyOwnedEmissions.toFixed(1)} kg CO₂
              </div>
              <div className="text-sm text-slate-600">Company Owned Emissions</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-orange-50 to-red-50 border-orange-200">
          <CardContent className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600 mb-2">
                {totals.totalEmissions.toFixed(1)} kg CO₂
              </div>
              <div className="text-sm text-slate-600">Total Emissions</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Cost vs Emissions Comparison by Category */}
      {scatterData && (scatterData.upstream.length > 0 || scatterData.downstream.length > 0 || scatterData.company_owned.length > 0) && (
        <Card className="bg-white/70 border-slate-200 backdrop-blur-sm shadow-lg">
          <CardHeader>
            <CardTitle className="text-slate-800 text-xl flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              Cost vs Carbon Emissions by Category
            </CardTitle>
            <CardDescription className="text-slate-600">
              Compare the financial cost and environmental impact across different transportation categories
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={[
                  {
                    category: 'Upstream',
                    cost: scatterData.upstream.reduce((sum, item) => sum + item.cost, 0),
                    emissions: scatterData.upstream.reduce((sum, item) => sum + item.emissions, 0),
                    count: scatterData.upstream.length
                  },
                  {
                    category: 'Downstream',
                    cost: scatterData.downstream.reduce((sum, item) => sum + item.cost, 0),
                    emissions: scatterData.downstream.reduce((sum, item) => sum + item.emissions, 0),
                    count: scatterData.downstream.length
                  },
                  {
                    category: 'Company Owned',
                    cost: scatterData.company_owned.reduce((sum, item) => sum + item.cost, 0),
                    emissions: scatterData.company_owned.reduce((sum, item) => sum + item.emissions, 0),
                    count: scatterData.company_owned.length
                  }
                ]}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="category"
                  stroke="#475569"
                  fontSize={12}
                  fontWeight={600}
                />
                <YAxis
                  yAxisId="left"
                  stroke="#10b981"
                  fontSize={12}
                  label={{ value: 'Cost (₹)', angle: -90, position: 'insideLeft', style: { fill: '#10b981' } }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke="#f59e0b"
                  fontSize={12}
                  label={{ value: 'Emissions (kg CO₂)', angle: 90, position: 'insideRight', style: { fill: '#f59e0b' } }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length > 0) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-4 border border-slate-200 rounded-lg shadow-lg">
                          <p className="font-bold text-slate-800 mb-2">{data.category}</p>
                          <p className="text-sm text-emerald-600 font-semibold">Cost: ₹{data.cost.toFixed(2)}</p>
                          <p className="text-sm text-orange-600 font-semibold">Emissions: {data.emissions.toFixed(2)} kg CO₂</p>
                          <p className="text-xs text-slate-500 mt-1">{data.count} shipment(s)</p>
                          <div className="mt-2 pt-2 border-t border-slate-200">
                            <p className="text-xs text-slate-600">
                              Cost per kg CO₂: ₹{(data.cost / data.emissions).toFixed(2)}
                            </p>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend
                  wrapperStyle={{ paddingTop: '20px' }}
                  iconType="rect"
                />
                <Bar
                  yAxisId="left"
                  dataKey="cost"
                  fill="#10b981"
                  name="Total Cost (₹)"
                  radius={[8, 8, 0, 0]}
                />
                <Bar
                  yAxisId="right"
                  dataKey="emissions"
                  fill="#f59e0b"
                  name="Total Emissions (kg CO₂)"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>

            {/* Summary Cards */}
            <div className="grid grid-cols-3 gap-4 mt-6">
              {[
                { name: 'Upstream', color: 'blue', data: scatterData.upstream },
                { name: 'Downstream', color: 'green', data: scatterData.downstream },
                { name: 'Company Owned', color: 'purple', data: scatterData.company_owned }
              ].map((cat) => {
                const totalCost = cat.data.reduce((sum, item) => sum + item.cost, 0);
                const totalEmissions = cat.data.reduce((sum, item) => sum + item.emissions, 0);
                const avgCostPerKg = totalEmissions > 0 ? totalCost / totalEmissions : 0;

                return (
                  <div key={cat.name} className={`p-4 rounded-lg border-2 border-${cat.color}-200 bg-${cat.color}-50`}>
                    <h4 className={`font-semibold text-${cat.color}-800 mb-2`}>{cat.name}</h4>
                    <div className="space-y-1">
                      <p className="text-xs text-slate-600">Total Cost: <span className="font-bold">₹{totalCost.toFixed(2)}</span></p>
                      <p className="text-xs text-slate-600">Total Emissions: <span className="font-bold">{totalEmissions.toFixed(2)} kg</span></p>
                      <p className="text-xs text-slate-600">Cost/Emission: <span className="font-bold">₹{avgCostPerKg.toFixed(2)}/kg</span></p>
                      <p className="text-xs text-slate-500">{cat.data.length} shipment(s)</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      {prepareChartData().length > 0 && (
        <div className="grid grid-cols-1 gap-6">
          {/* GHG Category Emissions Pie Chart */}
          <Card className="bg-white/70 border-slate-200 backdrop-blur-sm shadow-lg">
            <CardHeader>
              <CardTitle className="text-blue-700">Emissions Distribution by GHG Category</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Upstream', value: totals.upstreamEmissions, fill: '#3b82f6' },
                      { name: 'Downstream', value: totals.downstreamEmissions, fill: '#10b981' },
                      { name: 'Company Owned', value: totals.companyOwnedEmissions, fill: '#8b5cf6' }
                    ].filter(item => item.value > 0)}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {[
                      { name: 'Upstream', value: totals.upstreamEmissions, fill: '#3b82f6' },
                      { name: 'Downstream', value: totals.downstreamEmissions, fill: '#10b981' },
                      { name: 'Company Owned', value: totals.companyOwnedEmissions, fill: '#8b5cf6' }
                    ].filter(item => item.value > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#ffffff', 
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      color: '#1e293b'
                    }}
                    formatter={(value, name) => [
                      `${value.toFixed(2)} kg CO₂`, 
                      'Emissions'
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Recent Shipments Table */}
      <Card data-testid="dashboard-section" className="bg-white/70 border-slate-200 backdrop-blur-sm shadow-lg">
        <CardHeader>
          <CardTitle className="text-blue-700">All Shipments</CardTitle>
          <CardDescription className="text-slate-600">
            Complete list of calculated shipments with emissions and costs
          </CardDescription>
        </CardHeader>
        <CardContent>
          {shipments.length === 0 ? (
            <div className="text-center py-8 text-slate-600">
              No shipments calculated yet. Go to Calculator tab to create your first shipment.
            </div>
          ) : (
            <div className="space-y-4">
              {/* Multi-select Header */}
              <div className="flex items-center justify-between p-4 bg-slate-100 rounded-lg border border-slate-200">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={selectedShipments.length === shipments.length && shipments.length > 0}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                  />
                  <span className="text-sm text-slate-600">
                    {selectedShipments.length > 0 
                      ? `${selectedShipments.length} shipment(s) selected` 
                      : 'Select all shipments'
                    }
                  </span>
                </div>
                {selectedShipments.length > 0 && (
                  <Button
                    onClick={handleBulkDelete}
                    disabled={loading}
                    variant="destructive"
                    size="sm"
                    className="bg-red-500 hover:bg-red-600"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Selected ({selectedShipments.length})
                  </Button>
                )}
              </div>

              {shipments.map((shipment) => (
                <Card key={shipment.id} className="border-l-4 border-l-blue-500 bg-slate-50/80 border-slate-200">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <input
                        type="checkbox"
                        checked={selectedShipments.includes(shipment.id)}
                        onChange={(e) => handleSelectShipment(shipment.id, e.target.checked)}
                        className="w-4 h-4 mt-1 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                      />
                      <div className="flex-1">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div>
                        <h3 className="font-semibold text-lg text-slate-800">{shipment.good.name}</h3>
                        <p className="text-sm text-slate-600">
                          {shipment.good.quantity} {shipment.good.unit} • {shipment.good.ghg_category}
                        </p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-emerald-600">
                          {shipment.total_distance?.toFixed(1)} km
                        </div>
                        <div className="text-sm text-slate-600">Total Distance</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          ₹{shipment.total_cost?.toFixed(2)}
                        </div>
                        <div className="text-sm text-slate-600">Total Cost</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-orange-600">
                          {shipment.total_emissions?.toFixed(2)} kg CO₂
                        </div>
                        <div className="text-sm text-slate-600">Total Emissions</div>
                      </div>
                    </div>
                    
                        <div className="mt-4 pt-4 border-t border-slate-200">
                          <h4 className="font-medium text-slate-700 mb-3">Transport Legs:</h4>
                      
                      <div className="space-y-2">
                        {shipment.transport_legs.map((leg, index) => {
                          const Icon = {
                            road: Truck,
                            rail: Train,
                            air: Plane,
                            water: Ship
                          }[leg.transport_mode];
                          return (
                            <div key={index} className="flex items-center gap-2 text-sm text-slate-600">
                              <Icon className="h-4 w-4 text-blue-600" />
                              <span>
                                {leg.from_location.address} → {leg.to_location.address} 
                                ({leg.distance_km?.toFixed(1)} km via {leg.vehicle_type})
                              </span>
                            </div>
                          );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Admin Panel Component
const AdminPanel = () => {
  const [emissionFactors, setEmissionFactors] = useState([]);
  const [newFactor, setNewFactor] = useState({
    transport_mode: '',
    vehicle_type: '',
    emission_factor: '',
    unit: 'kgCO2/tonne-km'
  });

  useEffect(() => {
    loadEmissionFactors();
  }, []);

  const loadEmissionFactors = async () => {
    try {
      const response = await axios.get(`${API}/emission-factors`);
      setEmissionFactors(response.data);
    } catch (error) {
      console.error('Error loading emission factors:', error);
    }
  };

  const handleFactorChange = (field, value) => {
    setNewFactor(prev => ({ ...prev, [field]: value }));
  };

  const addEmissionFactor = async () => {
    if (!newFactor.transport_mode || !newFactor.vehicle_type || !newFactor.emission_factor) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      await axios.post(`${API}/emission-factors`, {
        ...newFactor,
        emission_factor: parseFloat(newFactor.emission_factor)
      });
      
      setNewFactor({
        transport_mode: '',
        vehicle_type: '',
        emission_factor: '',
        unit: 'kgCO2/tonne-km'
      });
      
      await loadEmissionFactors();
      toast.success('Emission factor added successfully');
    } catch (error) {
      console.error('Error adding emission factor:', error);
      toast.error('Error adding emission factor');
    }
  };

  const deleteEmissionFactor = async (factorId) => {
    try {
      await axios.delete(`${API}/emission-factors/${factorId}`);
      await loadEmissionFactors();
      toast.success('Emission factor deleted successfully');
    } catch (error) {
      console.error('Error deleting emission factor:', error);
      toast.error('Error deleting emission factor');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto py-8 px-4">
        <div className="text-center mb-8">
          <div className="flex justify-between items-center mb-4">
            <a href="/" className="text-sm text-blue-600 hover:text-blue-500 transition-colors" data-testid="home-link">
              ← Back to Calculator
            </a>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              Admin Panel
            </h1>
            <div></div>
          </div>
          <p className="text-lg text-slate-600">
            Manage emission factors and vehicle types
          </p>
        </div>

        <Card data-testid="admin-panel" className="bg-white/70 border-slate-200 backdrop-blur-sm shadow-lg">
          <CardHeader>
            <CardTitle className="text-blue-700">Emission Factors Management</CardTitle>
            <CardDescription className="text-slate-600">
              Add, edit, or delete emission factors for different transport modes and vehicle types
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Add New Emission Factor */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div>
                <Label htmlFor="transport-mode" className="text-slate-700">Transport Mode</Label>
                <Select 
                  value={newFactor.transport_mode} 
                  onValueChange={(value) => handleFactorChange('transport_mode', value)}
                >
                  <SelectTrigger data-testid="admin-transport-mode" className="bg-white/80 border-slate-300 text-slate-800">
                    <SelectValue placeholder="Select mode" />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-slate-200">
                    <SelectItem value="road">Road</SelectItem>
                    <SelectItem value="rail">Rail</SelectItem>
                    <SelectItem value="air">Air</SelectItem>
                    <SelectItem value="water">Water</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="vehicle-type" className="text-slate-700">Vehicle Type</Label>
                <Input
                  id="vehicle-type"
                  value={newFactor.vehicle_type}
                  onChange={(e) => handleFactorChange('vehicle_type', e.target.value)}
                  placeholder="e.g., Heavy Truck"
                  data-testid="admin-vehicle-type"
                  className="bg-white/80 border-slate-300 text-slate-800 placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <Label htmlFor="emission-factor" className="text-slate-700">Emission Factor</Label>
                <Input
                  id="emission-factor"
                  type="number"
                  step="0.001"
                  value={newFactor.emission_factor}
                  onChange={(e) => handleFactorChange('emission_factor', e.target.value)}
                  placeholder="0.15"
                  data-testid="admin-emission-factor"
                  className="bg-white/80 border-slate-300 text-slate-800 placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <Label htmlFor="unit" className="text-slate-700">Unit</Label>
                <Select 
                  value={newFactor.unit} 
                  onValueChange={(value) => handleFactorChange('unit', value)}
                >
                  <SelectTrigger data-testid="admin-unit" className="bg-white/80 border-slate-300 text-slate-800">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-slate-200">
                    <SelectItem value="kgCO2/tonne-km">kgCO2/tonne-km</SelectItem>
                    <SelectItem value="gCO2/kg-km">gCO2/kg-km</SelectItem>
                    <SelectItem value="kgCO2/km">kgCO2/km</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-end">
                <Button 
                  onClick={addEmissionFactor} 
                  className="w-full bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 transition-all duration-300" 
                  data-testid="add-emission-factor-btn"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Factor
                </Button>
              </div>
            </div>

            <Separator className="bg-slate-200" />

            {/* Existing Emission Factors */}
            <div className="space-y-3">
              {emissionFactors.map((factor) => (
                <div key={factor.id} className="flex items-center justify-between p-4 bg-slate-50/80 rounded-lg border border-slate-200">
                  <div className="grid grid-cols-4 gap-4 flex-1">
                    <div>
                      <span className="font-medium text-blue-600">{factor.transport_mode}</span>
                    </div>
                    <div>
                      <span className="text-slate-800">{factor.vehicle_type}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">{factor.emission_factor} {factor.unit}</span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteEmissionFactor(factor.id)}
                    data-testid={`delete-factor-${factor.id}`}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<TransportCalculator />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="*" element={<TransportCalculator />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;