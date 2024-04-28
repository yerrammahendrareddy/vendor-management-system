from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from vendors.views import VendorViewSet, PurchaseOrderViewSet, HistoricalPerformanceViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.authtoken.views import obtain_auth_token
# Default Router setup for REST API endpoints
router = DefaultRouter()
router.register(r'vendors', VendorViewSet)
router.register(r'purchase_orders', PurchaseOrderViewSet)
router.register(r'performance', HistoricalPerformanceViewSet)

# URL patterns include admin, API routes, and documentation views (Swagger and Redoc)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
