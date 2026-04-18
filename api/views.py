from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer
from django.db.models import Q
from django.db import transaction
from .models import KBEntry, QueryLog
from django.db.models import Count
from .permissions import IsAdminUser


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        if User.objects.filter(username=data['username']).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data['email']
        )

        # Signal auto-created the Company, now update company_name
        company = user.company
        company.company_name = data['company_name']
        company.save()

        # Generate JWT token
        refresh = RefreshToken.for_user(user)

        return Response({
            'username': user.username,
            'company_name': company.company_name,
            'api_key': company.api_key,
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        user = authenticate(
            username=data['username'],
            password=data['password']
        )

        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'company_name': user.company.company_name,
            'api_key': user.company.api_key,
        }, status=status.HTTP_200_OK)

class KBQueryView(APIView):
    def post(self, request):
        search_term = request.data.get('search', '').strip()

        if not search_term:
            return Response(
                {'error': 'search field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        company = request.user.company

        with transaction.atomic():
            results = KBEntry.objects.filter(
                Q(question__icontains=search_term) |
                Q(answer__icontains=search_term)
            )
            results_count = results.count()

            QueryLog.objects.create(
                company=company,
                search_term=search_term,
                results_count=results_count
            )

        results_data = [
            {
                'id': str(entry.id),
                'question': entry.question,
                'answer': entry.answer,
                'category': entry.category,
            }
            for entry in results
        ]

        return Response({
            'search': search_term,
            'count': results_count,
            'results': results_data,
        }, status=status.HTTP_200_OK)

class UsageSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_queries = QueryLog.objects.aggregate(
            total=Count('id')
        )['total']

        active_companies = QueryLog.objects.values(
            'company'
        ).distinct().count()

        top_search_terms = list(
            QueryLog.objects.values('search_term')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        return Response({
            'total_queries': total_queries,
            'active_companies': active_companies,
            'top_search_terms': top_search_terms,
        }, status=status.HTTP_200_OK)