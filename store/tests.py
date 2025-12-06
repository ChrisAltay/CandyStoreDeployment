
from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from .models import Candy, Order
from .views import order_create
from .cart import Cart

class OrderCreationTest(TestCase):
    def setUp(self):
        self.candy = Candy.objects.create(name="Test Candy", price=10.00, stock=100, description="desc", category="cat")
        self.factory = RequestFactory()

    def test_order_create_view(self):
        # Create a request
        request = self.factory.post('/store/order/create/')
        
        # Add session
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add user
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()
        
        # Add item to cart
        cart = Cart(request)
        cart.add(self.candy, quantity=2)
        
        # Execute view
        response = order_create(request)
        
        # Check response - verify it rendered the success page
        self.assertEqual(response.status_code, 200)
        
        # Check order created
        order = Order.objects.last()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_price, 20.00)
        self.assertEqual(order.status, 'Created')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.candy)
