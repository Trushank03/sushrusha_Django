from rest_framework import status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from datetime import datetime, timedelta
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from .models import Clinic
from .serializers import ClinicSerializer, ClinicCreateSerializer
from .models import ClinicService, ClinicInventory, ClinicAppointment, ClinicReview, ClinicDocument
from .serializers import ClinicServiceSerializer, ClinicInventorySerializer, ClinicAppointmentSerializer, ClinicReviewSerializer, ClinicDocumentSerializer
from .serializers import ClinicServiceCreateSerializer, ClinicInventoryCreateSerializer, ClinicAppointmentCreateSerializer, ClinicReviewCreateSerializer, ClinicDocumentCreateSerializer
from .serializers import ClinicSearchSerializer


class ClinicPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class ClinicViewSet(ModelViewSet):
    queryset = Clinic.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ClinicPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'state', 'is_verified', 'is_active']
    search_fields = ['name', 'description', 'city', 'specialties']
    ordering_fields = ['created_at', 'name', 'city']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ClinicCreateSerializer
        return ClinicSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Clinic.objects.all()
        if user.role == 'admin':
            return queryset.filter(admin=user)
        elif user.role in ['superadmin']:
            return queryset
        else:
            return queryset.filter(is_active=True)

    def perform_create(self, serializer):
        user = self.request.user
        # Only superadmin can create clinics
        if hasattr(user, 'role') and user.role == 'superadmin':
            serializer.save()
        else:
            raise PermissionDenied('Only superadmin can create eClinics.')

    def perform_update(self, serializer):
        serializer.save()


class ClinicServiceViewSet(ModelViewSet):
    """ViewSet for clinic service management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get services for specific clinic"""
        clinic_id = self.kwargs.get('clinic_id')
        return ClinicService.objects.filter(clinic_id=clinic_id)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ClinicServiceCreateSerializer
        return ClinicServiceSerializer


class ClinicInventoryViewSet(ModelViewSet):
    """ViewSet for clinic inventory management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get inventory for specific clinic"""
        clinic_id = self.kwargs.get('clinic_id')
        return ClinicInventory.objects.filter(clinic_id=clinic_id)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ClinicInventoryCreateSerializer
        return ClinicInventorySerializer


class ClinicAppointmentViewSet(ModelViewSet):
    """ViewSet for clinic appointment management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get appointments for specific clinic"""
        clinic_id = self.kwargs.get('clinic_id')
        user = self.request.user
        queryset = ClinicAppointment.objects.filter(clinic_id=clinic_id).select_related(
            'patient', 'doctor', 'clinic'
        )
        
        # Filter based on user role
        if user.role == 'patient':
            return queryset.filter(patient=user)
        elif user.role == 'doctor':
            return queryset.filter(doctor=user)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ClinicAppointmentCreateSerializer
        return ClinicAppointmentSerializer
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, clinic_id=None, pk=None):
        """Confirm appointment"""
        appointment = self.get_object()
        
        if appointment.status != 'scheduled':
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': 'Only scheduled appointments can be confirmed'
                },
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        appointment.status = 'confirmed'
        appointment.save()
        
        serializer = ClinicAppointmentSerializer(appointment)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Appointment confirmed successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, clinic_id=None, pk=None):
        """Cancel appointment"""
        appointment = self.get_object()
        
        if appointment.status in ['completed', 'cancelled']:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': 'Cannot cancel completed or already cancelled appointment'
                },
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        appointment.status = 'cancelled'
        appointment.save()
        
        serializer = ClinicAppointmentSerializer(appointment)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Appointment cancelled successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


class ClinicReviewViewSet(ModelViewSet):
    """ViewSet for clinic review management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get reviews for specific clinic"""
        clinic_id = self.kwargs.get('clinic_id')
        return ClinicReview.objects.filter(clinic_id=clinic_id).select_related('patient', 'clinic')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ClinicReviewCreateSerializer
        return ClinicReviewSerializer


class ClinicDocumentViewSet(ModelViewSet):
    """ViewSet for clinic document management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get documents for specific clinic"""
        clinic_id = self.kwargs.get('clinic_id')
        return ClinicDocument.objects.filter(clinic_id=clinic_id)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ClinicDocumentCreateSerializer
        return ClinicDocumentSerializer


class ClinicSearchView(APIView):
    """Search clinics with advanced filters"""
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        parameters=[
            OpenApiParameter('query', OpenApiTypes.STR, description='Search query'),
            OpenApiParameter('city', OpenApiTypes.STR, description='City filter'),
            OpenApiParameter('state', OpenApiTypes.STR, description='State filter'),
            OpenApiParameter('specialization', OpenApiTypes.STR, description='Specialization filter'),
            OpenApiParameter('service', OpenApiTypes.STR, description='Service filter'),
            OpenApiParameter('is_verified', OpenApiTypes.BOOL, description='Verified clinic filter'),
            OpenApiParameter('latitude', OpenApiTypes.FLOAT, description='Latitude for location search'),
            OpenApiParameter('longitude', OpenApiTypes.FLOAT, description='Longitude for location search'),
            OpenApiParameter('radius_km', OpenApiTypes.FLOAT, description='Search radius in kilometers'),
        ],
        responses={200: ClinicSerializer(many=True)},
        description="Search clinics with advanced filters"
    )
    def get(self, request):
        """Search clinics with advanced filters"""
        serializer = ClinicSearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid search parameters',
                    'details': serializer.errors
                },
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build query
        queryset = Clinic.objects.filter(is_active=True)
        
        # Apply role-based filtering
        user = request.user
        if user.role == 'patient':
            queryset = queryset.filter(is_verified=True)
        
        # Apply search filters
        search_data = serializer.validated_data
        
        if search_data.get('query'):
            query = search_data['query']
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(specialties__icontains=query)
            )
        
        if search_data.get('city'):
            queryset = queryset.filter(city__icontains=search_data['city'])
        
        if search_data.get('state'):
            queryset = queryset.filter(state__icontains=search_data['state'])
        
        if search_data.get('specialization'):
            queryset = queryset.filter(specialties__icontains=search_data['specialization'])
        
        if search_data.get('service'):
            queryset = queryset.filter(
                clinic_services__name__icontains=search_data['service']
            ).distinct()
        
        if search_data.get('is_verified') is not None:
            queryset = queryset.filter(is_verified=search_data['is_verified'])
        
        # Location-based search
        if search_data.get('latitude') and search_data.get('longitude'):
            lat = search_data['latitude']
            lng = search_data['longitude']
            radius = search_data.get('radius_km', 10)
            
            # Simple distance calculation (for more accuracy, use PostGIS)
            queryset = queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False
            ).extra(
                where=[
                    "6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude))) <= %s"
                ],
                params=[lat, lng, lat, radius]
            )
        
        # Paginate results
        paginator = ClinicPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ClinicSerializer(page, many=True)
            return paginator.get_paginated_response({
                'success': True,
                'data': serializer.data,
                'message': 'Search results retrieved successfully',
                'timestamp': timezone.now().isoformat()
            })
        
        serializer = ClinicSerializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Search results retrieved successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


class ClinicStatsView(APIView):
    """Get clinic statistics for dashboard"""
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={200: dict},
        description="Get clinic statistics for SuperAdmin dashboard"
    )
    def get(self, request):
        """Get clinic statistics for dashboard"""
        # Check permissions - only SuperAdmin can access
        if request.user.role != 'superadmin':
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'Only SuperAdmin can access clinic statistics'
                },
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Calculate basic statistics using database queries (efficient)
        total_clinics = Clinic.objects.count()
        active_clinics = Clinic.objects.filter(is_active=True).count()
        online_consultations = Clinic.objects.filter(accepts_online_consultations=True).count()
        inactive_clinics = Clinic.objects.filter(is_active=False).count()
        
        # Calculate monthly change (clinics created this month vs last month)
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        this_month_clinics = Clinic.objects.filter(created_at__gte=this_month_start).count()
        last_month_clinics = Clinic.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=this_month_start
        ).count()
        
        monthly_change = this_month_clinics - last_month_clinics
        
        stats_data = {
            'total_clinics': {
                'value': total_clinics,
                'change': f"{'+' if monthly_change >= 0 else ''}{monthly_change}"
            },
            'active_clinics': {
                'value': active_clinics,
                'change': '+0'  # Could calculate this if needed
            },
            'online_consultations': {
                'value': online_consultations,
                'change': '+0'  # Could calculate this if needed
            },
            'inactive_clinics': {
                'value': inactive_clinics,
                'change': '+0'  # Could calculate this if needed
            }
        }
        
        return Response({
            'success': True,
            'data': stats_data,
            'message': 'Clinic statistics retrieved successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


class ClinicAnalyticsView(APIView):
    """Get comprehensive analytics for SuperAdmin dashboard"""
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        responses={200: dict},
        description="Get comprehensive analytics for SuperAdmin dashboard"
    )
    def get(self, request):
        """Get comprehensive analytics data"""
        # Check permissions - only SuperAdmin can access
        if request.user.role != 'superadmin':
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'Only SuperAdmin can access clinic analytics'
                },
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Time periods
            now = timezone.now()
            last_7_days = now - timedelta(days=7)
            last_30_days = now - timedelta(days=30)
            last_90_days = now - timedelta(days=90)
            
            # Basic metrics
            total_clinics = Clinic.objects.count()
            active_clinics = Clinic.objects.filter(is_active=True).count()
            verified_clinics = Clinic.objects.filter(is_verified=True).count()
            online_clinics = Clinic.objects.filter(accepts_online_consultations=True).count()
            
            # Growth metrics
            new_clinics_7d = Clinic.objects.filter(created_at__gte=last_7_days).count()
            new_clinics_30d = Clinic.objects.filter(created_at__gte=last_30_days).count()
            new_clinics_90d = Clinic.objects.filter(created_at__gte=last_90_days).count()
            
            # Geographic analytics
            city_distribution = Clinic.objects.values('city').annotate(
                count=Count('id')
            ).order_by('-count')[:10] if Clinic.objects.exists() else []
            
            state_distribution = Clinic.objects.values('state').annotate(
                count=Count('id')
            ).order_by('-count')[:10] if Clinic.objects.exists() else []
            
            # Specialization analytics
            all_specialties = []
            if Clinic.objects.exists():
                for clinic in Clinic.objects.all():
                    if clinic.specialties:
                        all_specialties.extend(clinic.specialties)
            
            specialty_counts = {}
            for specialty in all_specialties:
                specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1
            
            top_specialties = sorted(specialty_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Monthly trends (last 12 months)
            monthly_trends = []
            for i in range(12):
                month_start = now.replace(day=1) - timedelta(days=30*i)
                month_end = month_start.replace(day=1) + timedelta(days=32)
                month_end = month_end.replace(day=1) - timedelta(days=1)
                
                count = Clinic.objects.filter(
                    created_at__gte=month_start,
                    created_at__lte=month_end
                ).count()
                
                monthly_trends.append({
                    'month': month_start.strftime('%B %Y'),
                    'count': count,
                    'period': month_start.strftime('%Y-%m')
                })
            
            monthly_trends.reverse()
            
            # Performance metrics
            verification_rate = round((verified_clinics / total_clinics * 100) if total_clinics > 0 else 0, 1)
            activation_rate = round((active_clinics / total_clinics * 100) if total_clinics > 0 else 0, 1)
            online_rate = round((online_clinics / total_clinics * 100) if total_clinics > 0 else 0, 1)
            
            # Recent activity
            recent_clinics = Clinic.objects.order_by('-created_at')[:5] if Clinic.objects.exists() else []
            recent_activity = []
            for clinic in recent_clinics:
                recent_activity.append({
                    'id': clinic.id,
                    'name': clinic.name,
                    'city': clinic.city,
                    'state': clinic.state,
                    'created_at': clinic.created_at.strftime('%Y-%m-%d'),
                    'is_verified': clinic.is_verified,
                    'is_active': clinic.is_active
                })
            
            analytics = {
                # Overview metrics
                'overview': {
                    'total_clinics': total_clinics,
                    'active_clinics': active_clinics,
                    'verified_clinics': verified_clinics,
                    'online_clinics': online_clinics,
                    'verification_rate': verification_rate,
                    'activation_rate': activation_rate,
                    'online_rate': online_rate
                },
                
                # Growth metrics
                'growth': {
                    'new_clinics_7d': new_clinics_7d,
                    'new_clinics_30d': new_clinics_30d,
                    'new_clinics_90d': new_clinics_90d,
                    'growth_rate_7d': round((new_clinics_7d / total_clinics * 100) if total_clinics > 0 else 0, 1),
                    'growth_rate_30d': round((new_clinics_30d / total_clinics * 100) if total_clinics > 0 else 0, 1),
                    'growth_rate_90d': round((new_clinics_90d / total_clinics * 100) if total_clinics > 0 else 0, 1)
                },
                
                # Geographic data
                'geographic': {
                    'cities': [{'city': item['city'], 'count': item['count']} for item in city_distribution],
                    'states': [{'state': item['state'], 'count': item['count']} for item in state_distribution]
                },
                
                # Specialization data
                'specializations': {
                    'top_specialties': [{'specialty': item[0], 'count': item[1]} for item in top_specialties],
                    'total_specialties': len(specialty_counts)
                },
                
                # Trends
                'trends': {
                    'monthly_growth': monthly_trends,
                    'last_updated': now.strftime('%Y-%m-%d %H:%M:%S')
                },
                
                # Recent activity
                'recent_activity': recent_activity
            }
            
            return Response({
                'success': True,
                'data': analytics,
                'message': 'Analytics data retrieved successfully',
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'code': 'ANALYTICS_ERROR',
                    'message': f'Failed to fetch analytics: {str(e)}'
                },
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NearbyClinicView(APIView):
    """Find nearby clinics"""
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        parameters=[
            OpenApiParameter('latitude', OpenApiTypes.FLOAT, description='User latitude', required=True),
            OpenApiParameter('longitude', OpenApiTypes.FLOAT, description='User longitude', required=True),
            OpenApiParameter('radius_km', OpenApiTypes.FLOAT, description='Search radius in kilometers', default=10),
            OpenApiParameter('specialization', OpenApiTypes.STR, description='Specialization filter'),
        ],
        responses={200: ClinicSerializer(many=True)},
        description="Find nearby clinics based on location"
    )
    def get(self, request):
        """Find nearby clinics"""
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius_km = float(request.query_params.get('radius_km', 10))
        specialization = request.query_params.get('specialization')
        
        if not latitude or not longitude:
            return Response({
                'success': False,
                'error': {
                    'code': 'MISSING_PARAMETERS',
                    'message': 'Latitude and longitude are required'
                },
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            lat = float(latitude)
            lng = float(longitude)
        except ValueError:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_COORDINATES',
                    'message': 'Invalid latitude or longitude'
                },
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find nearby clinics
        queryset = Clinic.objects.filter(
            is_active=True,
            is_verified=True,
            latitude__isnull=False,
            longitude__isnull=False
        ).extra(
            select={
                'distance': "6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude)))"
            },
            select_params=[lat, lng, lat],
            where=[
                "6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude))) <= %s"
            ],
            params=[lat, lng, lat, radius_km],
            order_by=['distance']
        )
        
        # Apply specialization filter if provided
        if specialization:
            queryset = queryset.filter(specialties__icontains=specialization)
        
        serializer = ClinicSerializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Nearby clinics retrieved successfully',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)



