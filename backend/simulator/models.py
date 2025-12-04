from django.db import models
from django.utils import timezone
import json

class BaseStation(models.Model):
    """5G Base Station configuration"""
    
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    height_m = models.FloatField(default=25.0, help_text="Antenna height in meters")
    
    frequency_ghz = models.FloatField(default=3.5, help_text="Carrier frequency in GHz")
    tx_power_dbm = models.FloatField(default=43.0, help_text="Transmit power in dBm")
    antenna_gain_dbi = models.FloatField(default=17.0, help_text="Antenna gain in dBi")
    
    azimuth = models.FloatField(default=0, help_text="Antenna azimuth in degrees")
    beamwidth_horizontal = models.FloatField(default=65, help_text="Horizontal beamwidth in degrees")
    beamwidth_vertical = models.FloatField(default=10, help_text="Vertical beamwidth in degrees")
    
    sector_count = models.IntegerField(default=3, choices=[(1, 'Omni'), (3, '3-Sector'), (6, '6-Sector')])
    
    is_active = models.BooleanField(default=True)
    operator = models.CharField(max_length=50, blank=True, help_text="e.g., Safaricom, Airtel")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"
    
    def to_dict(self):
        """Convert to dictionary for calculations"""
        return {
            'id': self.id,
            'name': self.name,
            'lat': self.latitude,
            'lon': self.longitude,
            'height': self.height_m,
            'tx_power_dbm': self.tx_power_dbm,
            'antenna_gain_dbi': self.antenna_gain_dbi,
            'frequency_ghz': self.frequency_ghz,
        }


class Building(models.Model):
    """Building footprint with height"""
    
    osm_id = models.BigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=200, blank=True)
    
    geometry = models.JSONField(help_text="GeoJSON polygon")
    height_m = models.FloatField(default=15.0, help_text="Building height in meters")
    
    building_type = models.CharField(
        max_length=50,
        choices=[
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
            ('industrial', 'Industrial'),
            ('public', 'Public'),
            ('other', 'Other'),
        ],
        default='other'
    )
    
    floors = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['building_type']),
        ]
        
    def __str__(self):
        return f"Building {self.osm_id or self.id} ({self.height_m}m)"


class Simulation(models.Model):
    """Simulation run configuration and results"""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    min_latitude = models.FloatField()
    max_latitude = models.FloatField()
    min_longitude = models.FloatField()
    max_longitude = models.FloatField()
    
    grid_resolution_m = models.FloatField(default=10.0, help_text="Grid spacing in meters")
    base_stations = models.ManyToManyField(BaseStation)
    frequency_ghz = models.FloatField(default=3.5)
    ue_height_m = models.FloatField(default=1.5, help_text="User equipment height")
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    coverage_percentage = models.FloatField(null=True, blank=True, help_text="% area with SINR > 0 dB")
    avg_sinr_db = models.FloatField(null=True, blank=True)
    avg_rsrp_dbm = models.FloatField(null=True, blank=True)
    results_file = models.FileField(upload_to='simulation_results/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} - {self.status}"


class SimulationResult(models.Model):
    """Individual grid point results"""
    
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name='results')
    latitude = models.FloatField()
    longitude = models.FloatField()
    rsrp_dbm = models.FloatField(help_text="Reference Signal Received Power")
    sinr_db = models.FloatField(help_text="Signal-to-Interference-plus-Noise Ratio")
    path_loss_db = models.FloatField()
    serving_base_station = models.ForeignKey(BaseStation, on_delete=models.SET_NULL, null=True)
    is_los = models.BooleanField(default=False, help_text="Line-of-Sight condition")
    
    class Meta:
        indexes = [
            models.Index(fields=['simulation', 'latitude', 'longitude']),
        ]
        unique_together = ['simulation', 'latitude', 'longitude]