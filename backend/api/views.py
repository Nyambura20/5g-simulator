from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import numpy as np

from simulator.models import BaseStation, Building, Simulation, SimulationResult
from .serializers import (BaseStationSerializer, BuildingSerializer,
                          SimulationSerializer, SimulationResultSerializer)
from simulator.propagation_models import PropagationModel, CoverageCalculator

class BaseStationViewSet(viewsets.ModelViewSet):
    queryset = BaseStation.objects.all()
    serializer_class = BaseStationSerializer

class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    
    @action(detail=False, methods=['get'])
    def within_bounds(self, request):
        """Get buildings within geographic bounds"""
        min_lat = float(request.query_params.get('min_lat', -1.2640))
        max_lat = float(request.query_params.get('max_lat', -1.2460))
        min_lon = float(request.query_params.get('min_lon', 36.7950))
        max_lon = float(request.query_params.get('max_lon', 36.8150))
        
        buildings = self.queryset.all()
        serializer = self.get_serializer(buildings, many=True)
        return Response(serializer.data)

class SimulationViewSet(viewsets.ModelViewSet):
    queryset = Simulation.objects.all()
    serializer_class = SimulationSerializer
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Execute the simulation"""
        simulation = self.get_object()
        
        try:
            simulation.status = 'running'
            simulation.save()
            
            base_stations = [bs.to_dict() for bs in simulation.base_stations.all()]
            
            if not base_stations:
                return Response(
                    {'error': 'No base stations configured'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            prop_model = PropagationModel(frequency_ghz=simulation.frequency_ghz)
            calculator = CoverageCalculator(prop_model)
            
            area_bounds = (
                simulation.min_longitude,
                simulation.min_latitude,
                simulation.max_longitude,
                simulation.max_latitude
            )
            
            results = calculator.generate_coverage_grid(
                area_bounds=area_bounds,
                grid_resolution_m=simulation.grid_resolution_m,
                base_stations=base_stations
            )
            
            rsrp_grid = results['rsrp']
            sinr_grid = results['sinr']
            
            valid_sinr = sinr_grid[sinr_grid > -np.inf]
            valid_rsrp = rsrp_grid[rsrp_grid > -np.inf]
            
            coverage_percentage = (np.sum(sinr_grid > 0) / sinr_grid.size) * 100
            avg_sinr = np.mean(valid_sinr) if len(valid_sinr) > 0 else 0
            avg_rsrp = np.mean(valid_rsrp) if len(valid_rsrp) > 0 else 0
            
            simulation.coverage_percentage = coverage_percentage
            simulation.avg_sinr_db = float(avg_sinr)
            simulation.avg_rsrp_dbm = float(avg_rsrp)
            simulation.status = 'completed'
            simulation.completed_at = timezone.now()
            simulation.save()
            
            lons = results['lons']
            lats = results['lats']
            
            sample_rate = 5
            for i in range(0, len(lats), sample_rate):
                for j in range(0, len(lons), sample_rate):
                    if sinr_grid[i, j] > -np.inf:
                        SimulationResult.objects.create(
                            simulation=simulation,
                            latitude=lats[i],
                            longitude=lons[j],
                            rsrp_dbm=float(rsrp_grid[i, j]),
                            sinr_db=float(sinr_grid[i, j]),
                            path_loss_db=0,
                            serving_base_station_id=int(results['best_server'][i, j]) + 1
                        )
            
            return Response({
                'status': 'completed',
                'coverage_percentage': coverage_percentage,
                'avg_sinr_db': avg_sinr,
                'avg_rsrp_dbm': avg_rsrp,
                'grid_shape': rsrp_grid.shape
            })
            
        except Exception as e:
            simulation.status = 'failed'
            simulation.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def heatmap_data(self, request, pk=None):
        """Get heatmap data for visualization"""
        simulation = self.get_object()
        results = SimulationResult.objects.filter(simulation=simulation)
        
        data = {
            'type': 'FeatureCollection',
            'features': []
        }
        
        for result in results:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [result.longitude, result.latitude]
                },
                'properties': {
                    'rsrp': result.rsrp_dbm,
                    'sinr': result.sinr_db,
                    'serving_bs': result.serving_base_station.name if result.serving_base_station else None
                }
            }
            data['features'].append(feature)
        
        return Response(data)