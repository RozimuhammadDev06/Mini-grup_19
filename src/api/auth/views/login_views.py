from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User
from api.auth.serializers.user_serializers import UserLoginSerializer


class LoginView(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        message = "Email or password wrong"
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                if user.is_active:
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        "message": "Login success",
                        "user": UserLoginSerializer(user).data,
                        "access": str(refresh.access_token),
                        "refresh": str(refresh)
                    }, status=status.HTTP_200_OK)
                message = "User not verified!"
        except User.DoesNotExist:
            pass

        return Response({
            "error": message,
        }, status=status.HTTP_400_BAD_REQUEST)