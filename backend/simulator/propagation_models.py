"""
5G Radio Propagation Models
Based on 3GPP TR 38.901 specifications
Author: Nyambura20
"""

import numpy as np
from scipy.spatial.distance import cdist
from shapely.geometry import LineString, Point
from typing import Tuple, List, Optional

class PropagationModel:
    """Base class for radio propagation calculations"""
    
    def __init__(self, frequency_ghz: float = 3.5):
        """
        Initialize propagation model
        
        Args:
            frequency_ghz: Carrier frequency in GHz (default 3.5 GHz for 5G)
        """
        self.frequency_ghz = frequency_ghz
        self.frequency_mhz = frequency_ghz * 1000
        self.wavelength = 3e8 / (frequency_ghz * 1e9)  # meters
        
    def haversine_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates (degrees)
            lat2, lon2: Second point coordinates (degrees)
            
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth radius in meters
        
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        
        a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def free_space_path_loss(self, distance_m: float) -> float:
        """
        Calculate Free-Space Path Loss (FSPL)
        
        Formula: FSPL(dB) = 32.45 + 20*log10(f_MHz) + 20*log10(d_km)
        
        Args:
            distance_m: Distance in meters
            
        Returns:
            Path loss in dB
        """
        if distance_m < 1:
            distance_m = 1  # Avoid log(0)
            
        distance_km = distance_m / 1000
        fspl = 32.45 + 20 * np.log10(self.frequency_mhz) + 20 * np.log10(distance_km)
        
        return fspl
    
    def calculate_3gpp_umi_los_probability(self, distance_2d: float) -> float:
        """
        Calculate LOS probability for Urban Micro (UMi) scenario
        Based on 3GPP TR 38.901 Table 7.4.2-1
        
        Args:
            distance_2d: 2D distance in meters
            
        Returns:
            LOS probability (0 to 1)
        """
        if distance_2d <= 18:
            return 1.0
        else:
            return 18/distance_2d + np.exp(-distance_2d/36) * (1 - 18/distance_2d)
    
    def calculate_3gpp_umi_los_path_loss(self, distance_3d: float, distance_2d: float,
                                          height_bs: float, height_ue: float) -> float:
        """
        Calculate 3GPP UMi LOS path loss
        3GPP TR 38.901 Table 7.4.1-1
        
        Args:
            distance_3d: 3D distance in meters
            distance_2d: 2D distance in meters
            height_bs: Base station height in meters
            height_ue: User equipment height in meters
            
        Returns:
            Path loss in dB
        """
        # Breakpoint distance
        h_E = 1.0  # Effective environment height
        h_BS_prime = height_bs - h_E
        h_UT_prime = height_ue - h_E
        
        d_BP_prime = 4 * h_BS_prime * h_UT_prime * self.frequency_ghz * 1e9 / 3e8
        
        if distance_2d < d_BP_prime:
            # Before breakpoint
            pl = 32.4 + 21 * np.log10(distance_3d) + 20 * np.log10(self.frequency_ghz)
        else:
            # After breakpoint
            pl = (32.4 + 40 * np.log10(distance_3d) + 20 * np.log10(self.frequency_ghz) 
                  - 9.5 * np.log10(d_BP_prime**2 + (height_bs - height_ue)**2))
        
        return pl
    
    def calculate_3gpp_umi_nlos_path_loss(self, distance_3d: float, distance_2d: float,
                                           height_bs: float, height_ue: float) -> float:
        """
        Calculate 3GPP UMi NLOS path loss
        3GPP TR 38.901 Table 7.4.1-1
        
        Args:
            distance_3d: 3D distance in meters
            distance_2d: 2D distance in meters
            height_bs: Base station height in meters
            height_ue: User equipment height in meters
            
        Returns:
            Path loss in dB
        """
        # First calculate LOS path loss
        pl_los = self.calculate_3gpp_umi_los_path_loss(distance_3d, distance_2d, 
                                                         height_bs, height_ue)
        
        # NLOS path loss formula
        pl_nlos = (35.3 * np.log10(distance_3d) + 22.4 + 21.3 * np.log10(self.frequency_ghz) 
                   - 0.3 * (height_ue - 1.5))
        
        # Take maximum of LOS and NLOS
        return max(pl_los, pl_nlos)
    
    def add_shadow_fading(self, path_loss_grid: np.ndarray, 
                          std_dev: float = 4.0,
                          correlation_distance: float = 10.0) -> np.ndarray:
        """
        Add spatially correlated log-normal shadow fading
        
        Args:
            path_loss_grid: Original path loss values (2D array)
            std_dev: Standard deviation in dB (4dB for LOS, 6dB for NLOS)
            correlation_distance: Decorrelation distance in meters
            
        Returns:
            Path loss with shadow fading
        """
        # Generate spatially correlated Gaussian random field
        # Using exponential correlation model
        
        shadow_fading = np.random.normal(0, std_dev, path_loss_grid.shape)
        
        # Apply exponential smoothing for spatial correlation
        # This is simplified; for production, use proper spatial correlation
        from scipy.ndimage import gaussian_filter
        sigma = correlation_distance / 10.0  # Approximate conversion
        shadow_fading = gaussian_filter(shadow_fading, sigma=sigma)
        
        return path_loss_grid + shadow_fading
    
    def calculate_received_power(self, tx_power_dbm: float, tx_gain_dbi: float,
                                 path_loss_db: float, rx_gain_dbi: float = 0) -> float:
        """
        Calculate received power using Friis transmission equation
        
        Args:
            tx_power_dbm: Transmit power in dBm
            tx_gain_dbi: Transmit antenna gain in dBi
            path_loss_db: Total path loss in dB
            rx_gain_dbi: Receive antenna gain in dBi (default 0 for UE)
            
        Returns:
            Received power in dBm
        """
        rx_power = tx_power_dbm + tx_gain_dbi + rx_gain_dbi - path_loss_db
        return rx_power


class RayTracing:
    """Ray-tracing engine for LOS/NLOS determination and reflection paths"""
    
    def __init__(self, buildings_gdf):
        """
        Initialize ray-tracer with building data
        
        Args:
            buildings_gdf: GeoDataFrame with building polygons and heights
        """
        self.buildings = buildings_gdf
        
    def is_line_of_sight(self, tx_point: Tuple[float, float], 
                         rx_point: Tuple[float, float],
                         tx_height: float, rx_height: float) -> bool:
        """
        Check if there's line-of-sight between transmitter and receiver
        
        Args:
            tx_point: (lon, lat) of transmitter
            rx_point: (lon, lat) of receiver
            tx_height: Transmitter height in meters
            rx_height: Receiver height in meters
            
        Returns:
            True if LOS exists, False otherwise
        """
        # Create LineString between TX and RX
        ray = LineString([tx_point, rx_point])
        
        # Check intersection with buildings
        for idx, building in self.buildings.iterrows():
            if ray.intersects(building.geometry):
                # Check if building is tall enough to block
                building_height = building.get('height', 15)  # Default 15m
                
                # Simple height check (can be improved with 3D geometry)
                avg_height = (tx_height + rx_height) / 2
                if building_height > avg_height:
                    return False  # NLOS
        
        return True  # LOS
    
    def find_reflected_paths(self, tx_point: Tuple[float, float], 
                            rx_point: Tuple[float, float],
                            max_reflections: int = 1) -> List[float]:
        """
        Find reflection paths (simplified single reflection)
        
        Args:
            tx_point: (lon, lat) of transmitter
            rx_point: (lon, lat) of receiver
            max_reflections: Maximum number of reflections to consider
            
        Returns:
            List of path losses for reflected paths
        """
        # Simplified implementation: single reflection from nearest building walls
        # For production, use image theory for precise reflection points
        
        reflected_paths = []
        
        # This is a placeholder - full implementation would:
        # 1. Find candidate reflection points on building walls
        # 2. Check if reflected path is clear
        # 3. Calculate path loss with reflection coefficient
        # 4. Apply phase shifts
        
        return reflected_paths


class CoverageCalculator:
    """Calculate coverage, SINR, and network metrics"""
    
    def __init__(self, propagation_model: PropagationModel, 
                 ray_tracer: Optional[RayTracing] = None):
        """
        Initialize coverage calculator
        
        Args:
            propagation_model: Instance of PropagationModel
            ray_tracer: Optional RayTracing instance for LOS/NLOS detection
        """
        self.prop_model = propagation_model
        self.ray_tracer = ray_tracer
        self.thermal_noise_dbm = -174  # dBm/Hz at 20°C
        
    def calculate_thermal_noise(self, bandwidth_hz: float, 
                                noise_figure_db: float = 7) -> float:
        """
        Calculate thermal noise power
        
        Args:
            bandwidth_hz: Signal bandwidth in Hz
            noise_figure_db: Receiver noise figure in dB
            
        Returns:
            Noise power in dBm
        """
        noise_power = (self.thermal_noise_dbm + 10 * np.log10(bandwidth_hz) 
                      + noise_figure_db)
        return noise_power
    
    def calculate_sinr(self, signal_power_dbm: float, 
                      interference_powers_dbm: List[float],
                      bandwidth_hz: float = 100e6) -> float:
        """
        Calculate Signal-to-Interference-plus-Noise Ratio
        
        Args:
            signal_power_dbm: Desired signal power in dBm
            interference_powers_dbm: List of interference powers in dBm
            bandwidth_hz: Signal bandwidth (default 100 MHz for 5G)
            
        Returns:
            SINR in dB
        """
        # Convert to linear scale
        signal_linear = 10 ** (signal_power_dbm / 10)
        
        interference_linear = sum([10 ** (p / 10) for p in interference_powers_dbm])
        
        noise_power_dbm = self.calculate_thermal_noise(bandwidth_hz)
        noise_linear = 10 ** (noise_power_dbm / 10)
        
        sinr_linear = signal_linear / (interference_linear + noise_linear)
        sinr_db = 10 * np.log10(sinr_linear)
        
        return sinr_db
    
    def generate_coverage_grid(self, area_bounds: Tuple[float, float, float, float],
                              grid_resolution_m: float,
                              base_stations: List[dict]) -> dict:
        """
        Generate coverage heatmap grid
        
        Args:
            area_bounds: (min_lon, min_lat, max_lon, max_lat)
            grid_resolution_m: Grid spacing in meters
            base_stations: List of BS dicts with 'lat', 'lon', 'height', 'tx_power', etc.
            
        Returns:
            Dictionary with grid coordinates, RSRP, SINR, best server
        """
        min_lon, min_lat, max_lon, max_lat = area_bounds
        
        # Convert lat/lon bounds to approximate meters
        # At equator, 1 degree ≈ 111 km
        lat_center = (min_lat + max_lat) / 2
        meters_per_deg_lat = 111320
        meters_per_deg_lon = 111320 * np.cos(np.radians(lat_center))
        
        # Create grid
        num_points_lon = int((max_lon - min_lon) * meters_per_deg_lon / grid_resolution_m)
        num_points_lat = int((max_lat - min_lat) * meters_per_deg_lat / grid_resolution_m)
        
        lons = np.linspace(min_lon, max_lon, num_points_lon)
        lats = np.linspace(min_lat, max_lat, num_points_lat)
        
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        
        # Initialize result grids
        rsrp_grid = np.full(lon_grid.shape, -np.inf)
        sinr_grid = np.full(lon_grid.shape, -np.inf)
        best_server_grid = np.full(lon_grid.shape, -1, dtype=int)
        
        ue_height = 1.5  # User equipment height in meters
        
        # Calculate coverage from each BS
        for bs_idx, bs in enumerate(base_stations):
            bs_lat, bs_lon = bs['lat'], bs['lon']
            bs_height = bs.get('height', 25)
            tx_power = bs.get('tx_power_dbm', 43)
            tx_gain = bs.get('antenna_gain_dbi', 17)
            
            # Calculate distance to all grid points (vectorized)
            distances = self.prop_model.haversine_distance(
                bs_lat, bs_lon, lat_grid, lon_grid
            )
            
            # Calculate 3D distance
            distance_3d = np.sqrt(distances**2 + (bs_height - ue_height)**2)
            
            # Determine LOS/NLOS (simplified - assume statistical)
            los_prob = self.prop_model.calculate_3gpp_umi_los_probability(distances)
            is_los = np.random.rand(*distances.shape) < los_prob
            
            # Calculate path loss
            path_loss = np.where(
                is_los,
                self.prop_model.calculate_3gpp_umi_los_path_loss(
                    distance_3d, distances, bs_height, ue_height
                ),
                self.prop_model.calculate_3gpp_umi_nlos_path_loss(
                    distance_3d, distances, bs_height, ue_height
                )
            )
            
            # Add shadow fading
            std_dev = np.where(is_los, 4.0, 6.0)
            # Simplified: use single std_dev
            path_loss = self.prop_model.add_shadow_fading(path_loss, std_dev=5.0)
            
            # Calculate received power
            rx_power = self.prop_model.calculate_received_power(
                tx_power, tx_gain, path_loss
            )
            
            # Update RSRP grid (keep maximum)
            better_signal = rx_power > rsrp_grid
            rsrp_grid = np.where(better_signal, rx_power, rsrp_grid)
            best_server_grid = np.where(better_signal, bs_idx, best_server_grid)
        
        # Calculate SINR (simplified: assume interference from other BSs)
        # For each point, serving cell is signal, others are interference
        for i in range(lon_grid.shape[0]):
            for j in range(lon_grid.shape[1]):
                serving_bs = best_server_grid[i, j]
                if serving_bs == -1:
                    continue
                
                signal_power = rsrp_grid[i, j]
                
                # Calculate interference from other BSs
                interference_powers = []
                for bs_idx, bs in enumerate(base_stations):
                    if bs_idx == serving_bs:
                        continue
                    
                    # Recalculate power from this BS (simplified)
                    bs_lat, bs_lon = bs['lat'], bs['lon']
                    dist = self.prop_model.haversine_distance(
                        bs_lat, bs_lon, lat_grid[i, j], lon_grid[i, j]
                    )
                    
                    # Quick path loss calc
                    pl = self.prop_model.free_space_path_loss(dist)
                    interf_power = bs.get('tx_power_dbm', 43) + bs.get('antenna_gain_dbi', 17) - pl
                    interference_powers.append(interf_power)
                
                sinr_grid[i, j] = self.calculate_sinr(signal_power, interference_powers)
        
        return {
            'lons': lons,
            'lats': lats,
            'rsrp': rsrp_grid,
            'sinr': sinr_grid,
            'best_server': best_server_grid
        }