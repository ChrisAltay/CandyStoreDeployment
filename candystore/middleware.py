from django.utils.deprecation import MiddlewareMixin


class NoCacheMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        """
        Add headers to prevent caching of pages, ensuring that
        logging out and pressing back doesn't show authenticated content.
        """
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response
