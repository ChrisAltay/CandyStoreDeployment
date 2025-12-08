from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User, AnonymousUser
from .models import Candy, Order
from .views import order_create
from .cart import Cart


class OrderCreationTest(TestCase):
    def setUp(self):
        self.candy = Candy.objects.create(
            name="Test Candy",
            price=10.00,
            stock=100,
            description="desc",
            category="cat",
        )
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_order_create_view_authenticated(self):
        # Create a request
        request = self.factory.post("/store/order/create/")

        # Add session
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        # Add user
        request.user = self.user

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
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_price, 20.00)

    def test_order_create_view_anonymous(self):
        # Create a request
        request = self.factory.post("/store/order/create/")

        # Add session
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        # Add user
        request.user = AnonymousUser()

        # Execute view
        response = order_create(request)

        # Check response - verify it 302 redirects to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


class FavoriteTest(TestCase):
    def setUp(self):
        self.candy = Candy.objects.create(
            name="Test Candy",
            price=10.00,
            stock=100,
            description="desc",
            category="cat",
        )
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username="testuser", password="password")

    def test_toggle_favorite_add(self):
        # Initial state: no favorite
        from .models import Favorite

        self.assertEqual(Favorite.objects.count(), 0)

        # Toggle ON
        response = self.client.post(f"/favorite/toggle/{self.candy.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["favorited"])
        self.assertEqual(Favorite.objects.count(), 1)
        self.assertEqual(Favorite.objects.first().user, self.user)
        self.assertEqual(Favorite.objects.first().candy, self.candy)

        # Toggle OFF
        response = self.client.post(f"/favorite/toggle/{self.candy.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["favorited"])
        self.assertEqual(Favorite.objects.count(), 0)

    def test_listing_favorites_account(self):
        from .models import Favorite

        Favorite.objects.create(user=self.user, candy=self.candy)

        response = self.client.get("/accounts/account/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Favorite Candies")
        self.assertContains(response, "Test Candy")
