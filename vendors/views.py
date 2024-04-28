from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from .models import Vendor, PurchaseOrder, HistoricalPerformance
from .serializers import VendorSerializer, PurchaseOrderSerializer, HistoricalPerformanceSerializer

class VendorViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Vendor objects within the database.
    Supports listing all vendors, retrieving, updating, and deleting a single vendor.
    Additional endpoint to retrieve performance metrics of a specific vendor.
    """
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    tags = ['Vendor Actions']

    @action(detail=True, methods=['get'], tags=['Vendor Performance'])
    def performance(self, request, pk=None):
        """
        Retrieves calculated performance metrics for a specific vendor such as on-time delivery rate,
        quality rating average, average response time, and fulfillment rate.

        Parameters:
        - request: HttpRequest object
        - pk: int, primary key of the vendor

        Returns:
        - Response: HttpResponse object containing the performance data or a not found error.
        """
        try:
            vendor = self.get_object()
            data = {
                'on_time_delivery_rate': vendor.on_time_delivery_rate(),
                'quality_rating_avg': vendor.quality_rating_avg(),
                'average_response_time': vendor.average_response_time(),
                'fulfillment_rate': vendor.fulfillment_rate()
            }
            return Response(data)
        except Vendor.DoesNotExist:
            raise NotFound(detail="Vendor not found.")

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    Manages CRUD operations for PurchaseOrder objects in the database.
    This viewset provides actions to list, retrieve, create, update, and delete purchase orders,
    as well as an action to acknowledge a purchase order.
    """
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    tags = ['Purchase Order Actions']

    @action(detail=True, methods=['post'], url_path='acknowledge', tags=['Purchase Order Acknowledgment'])
    def acknowledge(self, request, pk=None):
        """
        Acknowledges a purchase order by setting the acknowledgment date to the current time if it has not been acknowledged yet.

        Parameters:
        - request: HttpRequest object
        - pk: int, primary key of the purchase order

        Returns:
        - Response: HttpResponse object indicating success or failure of the acknowledgment.
        """
        try:
            purchase_order = self.get_object()
            if purchase_order.acknowledgment_date is not None:
                return Response({'error': 'Already acknowledged'}, status=status.HTTP_409_CONFLICT)

            purchase_order.acknowledgment_date = timezone.now()
            purchase_order.save()
            return Response({'status': 'Purchase order acknowledged successfully'}, status=status.HTTP_200_OK)
        except PurchaseOrder.DoesNotExist:
            raise NotFound(detail="Purchase order not found.")

class HistoricalPerformanceViewSet(viewsets.ModelViewSet):
    """
    Provides access to and management of historical performance data for vendors.
    Supports listing, retrieving, creating, and deleting historical performance records.
    """
    queryset = HistoricalPerformance.objects.all()
    serializer_class = HistoricalPerformanceSerializer
    tags = ['Performance Metrics']
