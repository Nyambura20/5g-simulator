from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BaseStationViewSet, BuildingViewSet, SimulationViewSet

router = DefaultRouter()
router.register(r'base-stations', BaseStationViewSet)
router.register(r'buildings', BuildingViewSet)
router.register(r'simulations', SimulationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]