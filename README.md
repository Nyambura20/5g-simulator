# 5G Radio Propagation Simulator for Westlands, Nairobi

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Django](https://img.shields.io/badge/django-5.0-green.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A comprehensive 5G radio propagation simulator implementing 3GPP TR 38.901 standards for urban micro (UMi) scenarios. This project simulates 5G network coverage in Westlands, Nairobi, using real-world building data from OpenStreetMap.

## 🎯 Features

### Core Capabilities
- **3GPP TR 38.901 Compliant Propagation Models**  
  - Urban Micro (UMi) LOS/NLOS path loss  
  - Shadow fading with spatial correlation  
  - SINR and RSRP calculations  
  - Realistic antenna patterns

- **Interactive Web Dashboard**  
  - Real-time coverage heatmaps  
  - Interactive Leaflet maps with OpenStreetMap  
  - Adjustable simulation parameters (frequency, grid resolution)  
  - Multiple base station management

- **Real-World Data Integration**  
  - OpenStreetMap building footprints  
  - Building height estimation from OSM data  
  - Geographic coordinates for Westlands, Nairobi

- **Network Optimization**  
  - Particle Swarm Optimization (PSO) for base station placement  
  - Coverage maximization  
  - Interference minimization

- **REST API**  
  - Full CRUD operations for base stations, buildings, simulations  
  - Simulation execution endpoint  
  - Heatmap data export (GeoJSON)

## 🏗️ Architecture

```
5g-simulator/
├── backend/                 # Django REST API
│   ├── config/             # Django settings
│   ├── simulator/          # Propagation engine
│   │   ├── propagation_models.py  # 3GPP TR 38.901 implementation
│   │   ├── models.py              # Database models
│   │   └── admin.py               # Django admin
│   ├── api/                # REST API
│   │   ├── views.py        # API endpoints
│   │   ├── serializers.py  # DRF serializers
│   │   └── urls.py         # API routing
│   ├── optimizer/          # PSO optimization
│   │   └── pso_optimizer.py
│   ├── scripts/            # Data collection
│   │   └── collect_westlands_data.py
│   └── requirements.txt
│
└── frontend/               # React application
    ├── src/
    │   ├── pages/          # Dashboard component
    │   ├── services/       # API integration
    │   ├── App.jsx         # Main app
    │   └── main.jsx        # Entry point
    ├── package.json
    └── vite.config.js
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- pip and npm

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/Nyambura20/5g-simulator.git
cd 5g-simulator
git checkout foundation-setup
```

2. **Create Python virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Collect building data from OpenStreetMap**
```bash
python scripts/collect_westlands_data.py
```

7. **Start Django development server**
```bash
python manage.py runserver
```

Backend will be available at: **http://localhost:8000**

Django Admin: **http://localhost:8000/admin**

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

Frontend will be available at: **http://localhost:5173**

## 📖 Usage

### 1. Add Base Stations

Go to Django Admin (http://localhost:8000/admin) and add base stations:
- Name: e.g., "Sarit Centre BS"
- Latitude/Longitude: Westlands coordinates
- Frequency: 3.5 GHz (default for 5G)
- TX Power: 43 dBm (typical for macro cells)
- Antenna Gain: 17 dBi
- Height: 25m (typical tower height)

Or use the sample base stations created by the data collection script.

### 2. Run Simulation

1. Open the dashboard at http://localhost:5173
2. Adjust simulation parameters:
   - **Frequency**: 2.1 - 28 GHz (common 5G bands)
   - **Grid Resolution**: 5 - 50 meters
3. Click **"Run Simulation"**
4. View coverage heatmap on the interactive map
5. Check results summary:
   - Coverage percentage
   - Average SINR
   - Average RSRP

### 3. Interpret Results

**Color Coding on Map:**
- 🟢 **Green**: Excellent coverage (SINR > 20 dB)
- 🟡 **Yellow**: Good coverage (SINR 10-20 dB)
- 🟠 **Orange**: Fair coverage (SINR 0-10 dB)
- 🔴 **Red**: Poor coverage (SINR < 0 dB)

**SINR Interpretation:**
- `> 20 dB`: Excellent for high-speed 5G (100+ Mbps)
- `10-20 dB`: Good for video streaming (50-100 Mbps)
- `0-10 dB`: Fair for web browsing (10-50 Mbps)
- `< 0 dB`: Poor, unreliable connection

## 🔬 Technical Details

### Propagation Models

Implemented according to **3GPP TR 38.901 Release 16**:

**UMi LOS Path Loss:**
```
PL = 32.4 + 21*log10(d3D) + 20*log10(fc)  [d < d_BP]
PL = 32.4 + 40*log10(d3D) + 20*log10(fc) - 9.5*log10(d_BP^2 + (h_BS - h_UT)^2)  [d >= d_BP]
```

**UMi NLOS Path Loss:**
```
PL = 35.3*log10(d3D) + 22.4 + 21.3*log10(fc) - 0.3*(h_UT - 1.5)
```

**Shadow Fading:**
- LOS: σ = 4 dB
- NLOS: σ = 6 dB
- Spatially correlated using exponential model

### Frequency Bands Supported

| Band | Frequency | Use Case |
|------|-----------|----------|
| n1   | 2.1 GHz   | Wide area coverage |
| n78  | 3.5 GHz   | Mid-band 5G (default) |
| n257 | 28 GHz    | mmWave high-speed |

## 🔧 API Endpoints

### Base Stations
```
GET    /api/base-stations/          # List all
POST   /api/base-stations/          # Create new
GET    /api/base-stations/{id}/     # Retrieve
PUT    /api/base-stations/{id}/     # Update
DELETE /api/base-stations/{id}/     # Delete
```

### Simulations
```
GET    /api/simulations/                    # List all
POST   /api/simulations/                    # Create
GET    /api/simulations/{id}/               # Retrieve
POST   /api/simulations/{id}/run/           # Execute simulation
GET    /api/simulations/{id}/heatmap_data/  # Get GeoJSON heatmap
```

### Buildings
```
GET    /api/buildings/                      # List all
GET    /api/buildings/within_bounds/        # Filter by bbox
```

## 🛠️ Technologies

### Backend
- Django 5.0, Django REST Framework 3.14
- NumPy/SciPy, Pandas, GeoPandas
- OSMnx, PySwarms

### Frontend
- React 18.2, Material-UI 5.15
- Leaflet, Plotly, Axios, Vite

## 📝 License

MIT License

## 👨‍💻 Author

**Nyambura20** - [@Nyambura20](https://github.com/Nyambura20)

## 📚 References

1. 3GPP TR 38.901 V16.1.0 - "Study on channel model for frequencies from 0.5 to 100 GHz"
2. ITU-R M.2135-1 - "Guidelines for evaluation of radio interface technologies for IMT-Advanced"

---

**Made with ❤️ for better 5G network planning in Kenya
