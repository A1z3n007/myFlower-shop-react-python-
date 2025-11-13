from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        name = request.data.get("name") or ""
        email = (request.data.get("email") or "").lower().strip()
        password = request.data.get("password") or ""
        if not email or not password:
            return Response({"detail":"email/password required"}, status=400)
        if User.objects.filter(username=email).exists():
            return Response({"detail":"email already registered"}, status=400)
        user = User.objects.create(
            username=email, email=email,
            first_name=name,
            password=make_password(password),
        )
        return Response({"id": user.id, "email": user.email, "name": user.first_name})

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        return Response({"id":u.id,"email":u.email,"name":u.first_name})
