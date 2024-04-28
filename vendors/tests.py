from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from django.urls import reverse
from rest_framework.response import Response
from .models import Vendor, PurchaseOrder, HistoricalPerformance

class VendorModelTest(TestCase):
    def setUp(self):
        self.vendor = Vendor.objects.create(
            name="Test Vendor",
            contact_details="1234567890",
            address="123 Test St",
            vendor_code="V001"
        )

    def test_string_representation(self):
        self.assertEqual(str(self.vendor), "Test Vendor")

    def test_on_time_delivery_rate(self):
        PurchaseOrder.objects.create(
            po_number="PO001",
            vendor=self.vendor,
            order_date=timezone.now(),
            delivery_date=timezone.now(),  # Delivered exactly on time
            status='completed',
            items={"item1": 10},
            quantity=10
        )
        PurchaseOrder.objects.create(
            po_number="PO005",
            vendor=self.vendor,
            order_date=timezone.now() - timezone.timedelta(hours=2),
            delivery_date=timezone.now() - timezone.timedelta(hours=1),  # Delivered one hour late
            status='completed',
            items={"item2": 5},
            quantity=5
        )
        expected_rate = 50.0
        calculated_rate = self.vendor.on_time_delivery_rate()
        self.assertAlmostEqual(calculated_rate, expected_rate, places=1)

    def test_quality_rating_avg(self):
        PurchaseOrder.objects.create(
            po_number="PO002",
            vendor=self.vendor,
            order_date=timezone.now(),
            delivery_date=timezone.now() + timezone.timedelta(hours=1),
            status='completed',
            items={"item1": 10},
            quantity=10,
            quality_rating=5
        )
        self.assertEqual(self.vendor.quality_rating_avg(), 5.0)

    def test_fulfillment_rate(self):
        PurchaseOrder.objects.create(
            po_number="PO003",
            vendor=self.vendor,
            order_date=timezone.now(),
            delivery_date=timezone.now() + timezone.timedelta(hours=1),
            status='completed',
            items={"item1": 10},
            quantity=10
        )
        PurchaseOrder.objects.create(
            po_number="PO004",
            vendor=self.vendor,
            order_date=timezone.now(),
            delivery_date=timezone.now() + timezone.timedelta(hours=1),
            status='pending',
            items={"item1": 5},
            quantity=5
        )
        expected_rate = 50.0
        self.assertAlmostEqual(self.vendor.fulfillment_rate(), expected_rate)

class AuthenticatedAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='password')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.vendor = Vendor.objects.create(name="Test Vendor", contact_details="1234567890", address="123 Test St", vendor_code="V001")

class PurchaseOrderViewSetTest(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.purchase_order = PurchaseOrder.objects.create(
            vendor=self.vendor,
            po_number="PO1001",
            order_date=timezone.now(),
            delivery_date=timezone.now() + timezone.timedelta(days=1),
            items={"item1": 10},
            quantity=10,
            status='pending'
        )
        self.url = reverse('purchaseorder-detail', kwargs={'pk': self.purchase_order.pk})

    def test_acknowledge_purchase_order(self):
        response = self.client.post(f"{self.url}acknowledge/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Purchase order acknowledged successfully')

    def acknowledge(self, request, *args, **kwargs):
        purchase_order = self.get_object()
        if purchase_order.acknowledgment_date is not None:
            return Response({'error': 'Already acknowledged'}, status=status.HTTP_409_CONFLICT)

    def test_acknowledge_purchase_order_already_acknowledged(self):
        self.purchase_order.acknowledgment_date = timezone.now()
        self.purchase_order.save()
        response = self.client.post(f"{self.url}acknowledge/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

class HistoricalPerformanceViewSetTest(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.historical_perf = HistoricalPerformance.objects.create(
            vendor=self.vendor,
            on_time_delivery_rate=95.0,
            quality_rating_avg=4.5,
            average_response_time=2,
            fulfillment_rate=90.0
        )
        self.url = reverse('historicalperformance-list')

    def test_list_historical_performance(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_historical_performance(self):
        data = {
            'vendor': self.vendor.id,
            'on_time_delivery_rate': 90.0,
            'quality_rating_avg': 4.0,
            'average_response_time': 3,
            'fulfillment_rate': 85.0
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(HistoricalPerformance.objects.count(), 2)
