from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView

class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data['access']
            refresh_token = response.data['refresh']

            # Set HTTP-only secure cookies
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,       # JS cannot access this
                secure=True,         # Only sent over HTTPS
                samesite='Lax',      # CSRF protection
                max_age=300,         # 5 minutes (match your ACCESS_TOKEN_LIFETIME)
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=86400,       # 1 day (match REFRESH_TOKEN_LIFETIME)
            )

            # Don't expose tokens in response body
            del response.data['access']
            del response.data['refresh']

        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Read refresh token from cookie instead of request body
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            raise AuthenticationFailed('No refresh token found in cookies')

        # Inject into request data
        request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            response.set_cookie(
                key='access_token',
                value=response.data['access'],
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=300,
            )
            del response.data['access']

        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response({'message': 'Logged out'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
