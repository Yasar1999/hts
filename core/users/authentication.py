from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from .models import CustomUser
from rest_framework.decorators import APIView
from .serializers import CustomUserListSerializer
from drf_yasg import openapi


class ObtainJSONWebTokenExtended(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        data = request.data
        username = data.get('username', '')
        user_obj = CustomUser.objects.filter(username=username).first()

        if user_obj:
            if user_obj.is_active:
                serializer = self.get_serializer(data=data)

                if serializer.is_valid():
                    user = serializer.user
                    tokens = serializer.validated_data

                    # You can also set session expiry as needed
                    request.session.set_expiry(int(settings.DEFAULT_SESSION_EXPIRY_TIME))
                    
                    response_data = self.get_response_payload(tokens, user, request)
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response('User is inactive. Please contact the administrator.',
                                status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response(f'{username} user does not exist', status=status.HTTP_401_UNAUTHORIZED)

    def get_response_payload(self, tokens, user, request):
        """ Custom response payload """
        user_details = CustomUserListSerializer(user, context={'request': request}).data
        return {
            'access': tokens['access'],  # Access token
            'refresh': tokens['refresh'],  # Refresh token
            'user': user_details
        }


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh Token')
            },
            required=['refresh']
        ))
    def post(self, request):
        try:
            # Get the refresh token from the request data
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            
            # Blacklist the refresh token
            token.blacklist()

            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
