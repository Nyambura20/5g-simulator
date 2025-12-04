from django.contrib import admin
from .models import BaseStation, Building, Simulation, SimulationResult

@admin.register(BaseStation)
class BaseStationAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude', 'frequency_ghz', 'tx_power_dbm', 'operator', 'is_active']
    list_filter = ['operator', 'is_active', 'sector_count']
    search_fields = ['name', 'operator']

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['osm_id', 'name', 'building_type', 'height_m', 'floors']
    list_filter = ['building_type']
    search_fields = ['name', 'osm_id']

@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'coverage_percentage', 'avg_sinr_db', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'completed_at', 'coverage_percentage', 'avg_sinr_db', 'avg_rsrp_dbm']

@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = ['simulation', 'latitude', 'longitude', 'rsrp_dbm', 'sinr_db', 'is_los']
    list_filter = ['is_los', 'simulation']