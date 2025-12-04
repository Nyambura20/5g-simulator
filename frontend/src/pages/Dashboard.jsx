import React, { useState } from 'react';
import { Container, Slider, Button, Card, Typography } from '@mui/material';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';

const baseStations = [
  { position: [51.505, -0.09], sinr: 25 },
  { position: [51.515, -0.1], sinr: 15 },
  { position: [51.525, -0.11], sinr: 5 },
];

const getColor = (sinr) => {
  if (sinr > 20) return 'green';
  if (sinr > 10) return 'yellow';
  if (sinr > 0) return 'orange';
  return 'red';
};

const Dashboard = () => {
  const [frequency, setFrequency] = useState(2.1);
  const [gridResolution, setGridResolution] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  
  const runSimulation = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/simulate', { frequency, gridResolution });
      setResults(response.data);
    } catch (error) {
      console.error('Simulation error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <Typography variant="h4">5G Simulation Dashboard</Typography>
      
      <Slider 
        value={frequency} 
        min={2.1} 
        max={28} 
        onChange={(e, val) => setFrequency(val)} 
        valueLabelDisplay="auto" 
        label="Frequency (GHz)"
      />
      
      <Slider 
        value={gridResolution} 
        min={5} 
        max={50} 
        onChange={(e, val) => setGridResolution(val)} 
        valueLabelDisplay="auto" 
        label="Grid Resolution (m)"
      />

      <Button variant="contained" onClick={runSimulation} disabled={loading}>
        {loading ? 'Running...' : 'Run Simulation'}
      </Button>

      {results && (
        <Card>
          <Typography variant="h5">Results Summary:</Typography>
          <Typography>Coverage Percentage: {results.coverage}%</Typography>
          <Typography>Average SINR: {results.averageSinr} dB</Typography>
          <Typography>Average RSRP: {results.averageRsrp} dBm</Typography>
        </Card>
      )}

      <MapContainer center={[51.505, -0.09]} zoom={13} style={{ height: "400px", width: "100%" }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {baseStations.map((station, index) => (
          <Marker key={index} position={station.position} icon={L.divIcon({ className: 'marker', iconAnchor: [12.5, 41], popupAnchor: [1, -34], className: getColor(station.sinr) })}>
            <Popup>
              SINR: {station.sinr} dB
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </Container>
  );
};

export default Dashboard;