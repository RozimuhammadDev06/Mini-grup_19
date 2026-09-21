from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User
from api.auth.serializers import user_serializers


class RegisterViews(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        password2 = request.data.get("password2")

        if password != password2:
            return Response({
                "error": "Passwords not match"
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({
                "error": "Email already exists"
            }, status=status.HTTP_400_BAD_REQUEST)

        ser = user_serializers.UserCreateSerializer(data=request.data)
        if ser.is_valid(raise_exception=True):
            user = ser.save(username=email, is_active=True)
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Registered successfully",
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_201_CREATED)

        return Response({
            "error": "Something went wrong"
        }, status=status.HTTP_400_BAD_REQUEST)