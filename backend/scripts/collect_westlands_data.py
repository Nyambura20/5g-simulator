"""
Data Collection Script for Westlands, Nairobi
Fetches building data from OpenStreetMap
"""

import osmnx as ox
import geopandas as gpd
import json
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from simulator.models import Building, BaseStation

# Westlands area bounds
NORTH = -1.2460
SOUTH = -1.2640
EAST = 36.8150
WEST = 36.7950

def fetch_buildings_from_osm():
    """
    Fetch building footprints from OpenStreetMap for Westlands area
    """
    print("Fetching buildings from OpenStreetMap...")
    
    try:
        # Fetch building footprints
        buildings_gdf = ox.geometries_from_bbox(NORTH, SOUTH, EAST, WEST, {'building': True})
        
        print(f"Found {len(buildings_gdf)} buildings")
        
        saved_count = 0
        for idx, row in buildings_gdf.iterrows():
            try:
                osm_id = idx[1] if isinstance(idx, tuple) else idx
                
                geom = row.geometry
                if geom.geom_type == 'Polygon':
                    geojson = {
                        'type': 'Polygon',
                        'coordinates': [list(geom.exterior.coords)]
                    }
                elif geom.geom_type == 'MultiPolygon':
                    geojson = {
                        'type': 'MultiPolygon',
                        'coordinates': [[list(p.exterior.coords)] for p in geom.geoms]
                    }
                else:
                    continue
                
                height = 15.0
                if 'building:levels' in row and row['building:levels']:
                    try:
                        levels = int(row['building:levels'])
                        height = levels * 3.5
                    except:
                        pass
                
                building_type = 'other'
                if 'building' in row:
                    btype = str(row['building']).lower()
                    if btype in ['residential', 'apartments', 'house']:
                        building_type = 'residential'
                    elif btype in ['commercial', 'retail', 'office']:
                        building_type = 'commercial'
                
                name = row.get('name', '')
                
                Building.objects.update_or_create(
                    osm_id=osm_id,
                    defaults={
                        'name': name,
                        'geometry': geojson,
                        'height_m': height,
                        'building_type': building_type,
                    }
                )
                saved_count += 1
                
            except Exception as e:
                continue
        
        print(f"Successfully saved {saved_count} buildings to database")
        return saved_count
        
    except Exception as e:
        print(f"Error fetching data from OSM: {e}")
        return 0

def create_sample_base_stations():
    """
    Create sample base stations for Westlands area
    """
    sample_stations = [
        {
            'name': 'Westlands Square BS',
            'latitude': -1.2650,
            'longitude': 36.8050,
            'operator': 'Safaricom',
        },
        {
            'name': 'Sarit Centre BS',
            'latitude': -1.2580,
            'longitude': 36.7980,
            'operator': 'Safaricom',
        },
        {
            'name': 'ABC Place BS',
            'latitude': -1.2520,
            'longitude': 36.8100,
            'operator': 'Airtel',
        },
    ]
    
    print("Creating sample base stations...")
    for station in sample_stations:
        BaseStation.objects.update_or_create(
            name=station['name'],
            defaults=station
        )
    
    print(f"Created {len(sample_stations)} base stations")

if __name__ == '__main__':
    print("=" * 50)
    print("Westlands 5G Simulator - Data Collection")
    print("=" * 50)
    
    fetch_buildings_from_osm()
    create_sample_base_stations()
    
    print("\nData collection complete!")