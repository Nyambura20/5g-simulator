from rest_framework import serializers
from simulator.models import BaseStation, Building, Simulation, SimulationResult

class BaseStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseStation
        fields = '__all__'

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'

class SimulationSerializer(serializers.ModelSerializer):
    base_stations = BaseStationSerializer(many=True, read_only=True)
    base_station_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=BaseStation.objects.all(),
        source='base_stations'
    )
    
    class Meta:
        model = Simulation
        fields = '__all__'

class SimulationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationResult
        fields = '__all__'