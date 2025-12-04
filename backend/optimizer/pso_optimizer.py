"""
PSO-based Base Station Optimization for 5G Networks
Author: Nyambura20
"""

import numpy as np
from pyswarms.single.global_best import GlobalBestPSO
from simulator.propagation_models import PropagationModel, CoverageCalculator

class BaseStationOptimizer:
    """
    Optimize base station placement using Particle Swarm Optimization (PSO)
    """
    
    def __init__(self, area_bounds, n_base_stations=5, frequency_ghz=3.5):
        """
        Initialize optimizer
        
        Args:
            area_bounds: (min_lon, min_lat, max_lon, max_lat)
            n_base_stations: Number of base stations to optimize
            frequency_ghz: Carrier frequency in GHz
        """
        self.area_bounds = area_bounds
        self.n_base_stations = n_base_stations
        self.frequency_ghz = frequency_ghz
        
        min_lon, min_lat, max_lon, max_lat = area_bounds
        
        # PSO bounds: [lon1, lat1, lon2, lat2, ...]
        self.bounds_lower = np.array([min_lon, min_lat] * n_base_stations)
        self.bounds_upper = np.array([max_lon, max_lat] * n_base_stations)
        
        self.prop_model = PropagationModel(frequency_ghz=frequency_ghz)
        self.calculator = CoverageCalculator(self.prop_model)
        
    def objective_function(self, positions):
        """
        Objective function for PSO: Maximize coverage and minimize interference
        
        Args:
            positions: Array of shape (n_particles, 2*n_base_stations)
                      Each row: [lon1, lat1, lon2, lat2, ...]
        
        Returns:
            Array of fitness values (lower is better for PSO minimization)
        """
        n_particles = positions.shape[0]
        fitness = np.zeros(n_particles)
        
        for i in range(n_particles):
            # Extract base station positions
            pos = positions[i].reshape(self.n_base_stations, 2)
            
            # Create base station dictionaries
            base_stations = []
            for j, (lon, lat) in enumerate(pos):
                base_stations.append({
                    'id': j,
                    'name': f'BS_{j}',
                    'lat': lat,
                    'lon': lon,
                    'height': 25.0,
                    'tx_power_dbm': 43.0,
                    'antenna_gain_dbi': 17.0,
                    'frequency_ghz': self.frequency_ghz,
                })
            
            # Calculate coverage
            try:
                results = self.calculator.generate_coverage_grid(
                    area_bounds=self.area_bounds,
                    grid_resolution_m=20.0,  # Coarser grid for speed
                    base_stations=base_stations
                )
                
                sinr_grid = results['sinr']
                
                # Calculate metrics
                coverage_percentage = (np.sum(sinr_grid > 0) / sinr_grid.size) * 100
                avg_sinr = np.mean(sinr_grid[sinr_grid > -np.inf])
                
                # Fitness: Maximize coverage and SINR (minimize negative)
                fitness[i] = -(coverage_percentage + avg_sinr)
                
            except Exception as e:
                # Penalty for invalid configurations
                fitness[i] = 1e6
        
        return fitness
    
    def optimize(self, n_particles=30, n_iterations=50):
        """
        Run PSO optimization
        
        Args:
            n_particles: Number of particles in swarm
            n_iterations: Number of iterations
            
        Returns:
            Dictionary with optimal positions and metrics
        """
        dimensions = 2 * self.n_base_stations
        
        options = {'c1': 0.5, 'c2': 0.3, 'w': 0.9}  # PSO hyperparameters
        
        optimizer = GlobalBestPSO(
            n_particles=n_particles,
            dimensions=dimensions,
            options=options,
            bounds=(self.bounds_lower, self.bounds_upper)
        )
        
        cost, optimal_positions = optimizer.optimize(
            self.objective_function,
            iters=n_iterations
        )
        
        # Reshape optimal positions
        optimal_bs_positions = optimal_positions.reshape(self.n_base_stations, 2)
        
        # Create base station list
        optimal_base_stations = []
        for j, (lon, lat) in enumerate(optimal_bs_positions):
            optimal_base_stations.append({
                'id': j,
                'name': f'Optimized_BS_{j}',
                'lat': float(lat),
                'lon': float(lon),
                'height': 25.0,
                'tx_power_dbm': 43.0,
                'antenna_gain_dbi': 17.0,
                'frequency_ghz': self.frequency_ghz,
            })
        
        return {
            'optimal_positions': optimal_base_stations,
            'cost': float(cost),
            'iterations': n_iterations,
        }