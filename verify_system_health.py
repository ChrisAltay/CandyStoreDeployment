import os
import sys
import django
from django.conf import settings
from django.test import RequestFactory
from django.template.loader import render_to_string

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "candystore.settings")
django.setup()

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from store.models import Order, Candy, OrderItem
from store.views import order_status_api


def verify_system():
    print("Starting Final System Health Check...")

    # 1. Verification Data Setup
    user, _ = User.objects.get_or_create(username="verifier")
    candy, _ = Candy.objects.get_or_create(name="Test Candy", price=1.00)
    order = Order.objects.create(user=user, total_price=5.00)
    OrderItem.objects.create(order=order, product=candy, price=1.00, quantity=5)

    try:
        # 2. Test Template Rendering (Order Detail)
        # This checks for syntax errors in the template
        print(f"Testing Template Rendering for Order #{order.id}...")
        context = {"order": order}
        # We try to render just the block content or the whole thing?
        # Using render_to_string with the Request is best
        factory = RequestFactory()
        request = factory.get(f"/order/{order.id}/")
        from django.contrib.sessions.middleware import SessionMiddleware

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        request.user = user

        # We manually render to check for errors
        try:
            # Just loading the template checks syntax
            from django.template import loader

            t = loader.get_template("store/order_detail.html")
            content = t.render(context, request)
            print("PASS: order_detail.html renders successfully.")

            # Check if item name is in the output correctly (not literal {{)
            if "Test Candy" in content:
                if "{{ item.product.name }}" not in content:
                    print("PASS: Item name rendered correctly (no literal tags found).")
                else:
                    print("FAIL: Literal tag {{ item.product.name }} found in output!")
            else:
                print("FAIL: 'Test Candy' NAME MISSING from output!")
                # Find where h3 is and print it
                import re

                match = re.search(r"<h3[^>]*>.*?</h3>", content, re.DOTALL)
                if match:
                    print(f"DEBUG: Found h3 block: {match.group(0)}")
                else:
                    print("DEBUG: No h3 block found.")

        except Exception as e:
            print(f"FAIL: Template rendering error: {e}")

        # 3. Test API Endpoint
        print("Testing API Endpoint...")
        response = order_status_api(request, order.id)
        if response.status_code == 200:
            import json

            data = json.loads(response.content)
            print(f"PASS: API returned 200 OK. Status: {data['status']}")
        else:
            print(f"FAIL: API returned {response.status_code}")

    except Exception as main_e:
        print(f"FAIL: Unexpected error during verification: {main_e}")
    finally:
        # Cleanup
        order.delete()
        print("Cleanup complete.")


if __name__ == "__main__":
    verify_system()
