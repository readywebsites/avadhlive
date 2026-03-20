import re
import logging
from rest_framework import viewsets, filters, status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from .models import Project, Enquiry, JobOpening, JobApplication, Insight
from .serializers import ProjectSerializer, ProjectListSerializer, EnquirySerializer, ProjectMiniSerializer, JobOpeningSerializer, JobApplicationSerializer, InsightSerializer
from .filters import ProjectFilter # <-- Import the new filter
from collections import defaultdict
from django.shortcuts import render

logger = logging.getLogger(__name__)

def frontend(request):
    return render(request, "index.html")

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter # <-- Use the powerful filter class
    pagination_class = StandardResultsSetPagination
    search_fields = ['title', 'description', 'location', 'city', 'area', 'project_type', 'bhk'] # <-- Add full-text search
    ordering_fields = ['title', 'created_at', 'nav_order'] # <-- Allow ordering

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer

    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        """
        Custom endpoint to get available filter options for the frontend.
        This dynamically generates lists of unique locations, categories, and statuses.
        """
        queryset = self.get_queryset()
        cities = sorted(list(queryset.values_list('city', flat=True).distinct()))
        categories = [{'value': choice[0], 'label': choice[1]} for choice in Project.Category.choices]
        statuses = [{'value': choice[0], 'label': choice[1]} for choice in Project.Status.choices]

        return Response({
            'cities': [c for c in cities if c],
            'categories': categories,
            'statuses': statuses,
        })

class NavigationAPIView(APIView):
    """
    A custom API view to provide a structured JSON response for the website's navigation.
    This is designed to be the single source of truth, replacing the frontend's `navData.js`.
    """
    def get(self, request, *args, **kwargs):
        # 1. Fetch all relevant projects in a single, efficient query.
        projects = Project.objects.filter(
            category__in=[Project.Category.RESIDENTIAL, Project.Category.COMMERCIAL, Project.Category.INDUSTRIAL, Project.Category.FARMVILLE, Project.Category.CLUB],
            show_in_nav=True
        ).order_by('nav_order', 'title')

        # 2. Group projects dynamically by category and status.
        grouped_projects = defaultdict(lambda: defaultdict(list))
        for p in projects:
            grouped_projects[p.category][p.status].append(p)

        # 3. Serialize the grouped data.
        # We pass context={'request': request} so that ImageFields return absolute URLs
        serializer_context = {'request': request}

        res_ongoing_data = ProjectMiniSerializer(grouped_projects.get(Project.Category.RESIDENTIAL, {}).get(Project.Status.ONGOING, []), many=True, context=serializer_context).data
        res_completed_data = ProjectMiniSerializer(grouped_projects.get(Project.Category.RESIDENTIAL, {}).get(Project.Status.COMPLETED, []), many=True, context=serializer_context).data
        com_ongoing_data = ProjectMiniSerializer(grouped_projects.get(Project.Category.COMMERCIAL, {}).get(Project.Status.ONGOING, []), many=True, context=serializer_context).data
        com_completed_data = ProjectMiniSerializer(grouped_projects.get(Project.Category.COMMERCIAL, {}).get(Project.Status.COMPLETED, []), many=True, context=serializer_context).data

        # For industrial, combine all statuses into one list.
        industrial_projects_map = grouped_projects.get(Project.Category.INDUSTRIAL, {})
        industrial_projects_list = [p for sublist in industrial_projects_map.values() for p in sublist]
        industrial_data = ProjectMiniSerializer(industrial_projects_list, many=True, context=serializer_context).data

        # For farmville, combine all statuses into one list.
        farmville_projects_map = grouped_projects.get(Project.Category.FARMVILLE, {})
        farmville_projects_list = [p for sublist in farmville_projects_map.values() for p in sublist]
        farmville_data = ProjectMiniSerializer(farmville_projects_list, many=True, context=serializer_context).data

        # For clubs, combine all statuses into one list.
        club_projects_map = grouped_projects.get(Project.Category.CLUB, {})
        club_projects_list = [p for sublist in club_projects_map.values() for p in sublist]
        club_data = ProjectMiniSerializer(club_projects_list, many=True, context=serializer_context).data

        # 4. Construct the final data structure, matching the frontend's `navData.js`
        nav_data = [
            {'id': 'home', 'chapter': 1, 'label': 'Home'},
            {'id': 'about-us', 'chapter': 2, 'label': 'About Us'},
            {
                'id': 'residential',
                'chapter': 3,
                'label': 'Residential',
                'submenu': [
                    {
                        'id': 'res-ongoing',
                        'title': 'On-going Projects',
                        'projects': res_ongoing_data,
                        'viewAll': {'label': 'View All Residential', 'link': '/portfolio/residential'}
                    },
                    {
                        'id': 'res-completed',
                        'title': 'Completed Projects',
                        'projects': res_completed_data,
                        'viewAll': {'label': 'View All Completed', 'link': '/portfolio/residential'}
                    }
                ]
            },
            {
                'id': 'commercial',
                'chapter': 4,
                'label': 'Commercial',
                'submenu': [
                    {
                        'id': 'com-ongoing',
                        'title': 'On-going Projects',
                        'projects': com_ongoing_data,
                        'viewAll': {'label': 'View All Commercial', 'link': '/portfolio/commercial'}
                    },
                    {
                        'id': 'com-completed',
                        'title': 'Completed Projects',
                        'projects': com_completed_data,
                        'viewAll': {'label': 'View All Completed', 'link': '/portfolio/commercial'}
                    }
                ]
            },
            {
                'id': 'industrial',
                'chapter': 5,
                'label': 'Industrial',
                'submenu': [
                    {
                        'id': 'industrial-projects-section',
                        'title': 'Industrial Projects',
                        'projects': industrial_data,
                        'viewAll': {'label': 'View All Industrial', 'link': '/portfolio/industrial'}
                    }
                ]
            },
            {
                'id': 'farmville',
                'chapter': 6,
                'label': 'Farmville',
                'submenu': [
                    {
                        'id': 'farmville-projects-section',
                        'title': 'Farmville Projects',
                        'projects': farmville_data,
                        'viewAll': {'label': 'View All Farmville', 'link': '/portfolio/farmville'}
                    }
                ]
            },
            {
                'id': 'club',
                'chapter': 7,
                'label': 'Lifestyle Club',
                'submenu': [{
                    'id': 'club-projects-section',
                    'title': 'Exclusive Clubs',
                    'projects': club_data,
                    'viewAll': {'label': 'View All', 'link': '/portfolio/club'}
                }]
            },
            {'id': 'BLOG', 'chapter': 8, 'label': 'BLOG'},
            # The 'More' section can also be made dynamic with another model if needed.
            {
                'id': 'more', 'chapter': None, 'label': 'More', 'submenu': [
                    {'id': 'more-media', 'title': 'Media', 'link': '/media', 'isSimpleLink': True},
                    {'id': 'more-contact', 'title': 'Contact Us', 'link': '/contact', 'isSimpleLink': True},
                    {'id': 'more-careers', 'title': 'Careers', 'link': '/careers', 'isSimpleLink': True},
                ]
            },
        ]

        return Response(nav_data)

class EnquiryViewSet(viewsets.ModelViewSet):
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySerializer

class BookVisitAPIView(APIView):
    """
    Handles 'Book a Visit' form submissions from the frontend.
    This endpoint is public and exempt from CSRF checks.
    """
    permission_classes = [AllowAny]
    authentication_classes = [] # Disable session auth to bypass CSRF check

    def post(self, request, *args, **kwargs):
        data = request.data
        
        # Format the message to include visit details
        visit_info = (
            f"Visit Request\n"
            f"Date: {data.get('date')}\n"
            f"Time: {data.get('time')}\n"
            f"Project Type: {data.get('projectType')}\n"
            f"Project: {data.get('project')}\n"
            f"Message: {data.get('message', '')}"
        )

        # Map to Enquiry model fields
        enquiry_data = {
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'project_of_interest': data.get('project', ''),
            'message': visit_info
        }

        serializer = EnquirySerializer(data=enquiry_data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Visit scheduled successfully"}, status=201)
        return Response(serializer.errors, status=400)

class ContactAPIView(APIView):
    """
    API endpoint to handle 'Get In Touch' form submissions.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            
            # Extract fields
            name = data.get('name')
            phone = data.get('phone')
            email = data.get('email')
            project = data.get('project')
            subject = data.get('subject')
            message = data.get('message')

            # Combine subject and message for storage and email
            full_message = (
                f"Subject: {subject}\n"
                f"Project Interested In: {project or 'Not specified'}\n\n"
                f"Message:\n{message}"
            )

            # Map to Enquiry model fields and save to database
            enquiry_data = {
                'name': name,
                'email': email,
                'phone': phone,
                'project_of_interest': project,
                'message': full_message
            }

            serializer = EnquirySerializer(data=enquiry_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # Also send the email notification
            email_subject = f"New Contact Inquiry: {subject} - {name}"
            email_body = (
                f"Name: {name}\n"
                f"Phone: {phone}\n"
                f"Email: {email}\n"
                f"{'-'*20}\n"
                f"{full_message}"
            )

            # Send email
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[getattr(settings, 'CONTACT_EMAIL', settings.DEFAULT_FROM_EMAIL)],
                fail_silently=False,
            )

            return Response({"message": "Inquiry received successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Contact form error: {str(e)}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectFilterMetadataView(APIView):
    """
    Returns unique filter options based on the category (Residential, Commercial, Club).
    """
    def get(self, request):
        category = request.query_params.get('category', 'residential')
        
        # 1. Filter queryset by category
        queryset = Project.objects.filter(category__iexact=category)

        # 2. Extract Unique Cities
        cities = queryset.values_list('city', flat=True).distinct().order_by('city')
        cities = [c for c in cities if c]

        # 3. Extract Unique Project Types
        types = queryset.values_list('project_type', flat=True).distinct().order_by('project_type')
        # Modified to split comma-separated types into individual options
        raw_types = queryset.values_list('project_type', flat=True).exclude(project_type__isnull=True).distinct()
        type_set = set()
        for t_str in raw_types:
            # Split by comma or ampersand, trim whitespace, and add to set
            for single_type in re.split(r'[,&]', str(t_str)):
                clean_type = single_type.strip()
                if clean_type:
                    type_set.add(clean_type)
        types = sorted(list(type_set))

        # 4. Extract Unique BHK/SQFT Options based on category
        bhk_options = []
        if category.lower() == 'residential':
            bhk_raw = queryset.values_list('bhk', flat=True).exclude(bhk__isnull=True).distinct()
            bhk_set = set()
            for s in bhk_raw:
                for p in re.split(r'[&,]', str(s)):
                    clean_val = p.strip()
                    if clean_val and "BHK" in clean_val.upper():
                        bhk_set.add(clean_val)
            bhk_options = sorted(list(bhk_set))
        elif category.lower() == 'commercial':
            # For commercial, create Sq.Ft. ranges
            # Get all non-null min/max values from the new numeric fields
            all_sqft_values = list(queryset.values_list('area_sqft_min', 'area_sqft_max'))
            sqft_values = [v for pair in all_sqft_values for v in pair if v is not None]

            if sqft_values:
                ranges = [(0, 500), (501, 1000), (1001, 2000), (2001, 5000), (5001, float('inf'))]
                range_labels = {
                    (0, 500): "0-500 Sq.Ft.", (501, 1000): "501-1000 Sq.Ft.",
                    (1001, 2000): "1001-2000 Sq.Ft.", (2001, 5000): "2001-5000 Sq.Ft.",
                    (5001, float('inf')): "5001+ Sq.Ft."
                }
                active_ranges = {range_labels[r] for val in sqft_values for r in ranges if r[0] <= val <= r[1]}
                sort_map = {label: r[0] for r, label in range_labels.items()}
                bhk_options = sorted(list(active_ranges), key=lambda x: sort_map.get(x, 0))
        
        # 5. Build Hierarchical Area Mapping (City -> [Areas])
        area_mapping = {}
        area_data = queryset.values('city', 'area').distinct().order_by('area')
        
        for item in area_data:
            city_val = item.get('city')
            area = item.get('area')
            
            if city_val and area:
                if city_val not in area_mapping:
                    area_mapping[city_val] = []
                if area not in area_mapping[city_val]:
                    area_mapping[city_val].append(area)

        return Response({
            "category": category,
            "filters": {
                "city": cities,
                "type": types,
                "bhk": bhk_options,
                "area_map": area_mapping,
            }
        })

class JobOpeningViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for listing active job openings.
    """
    queryset = JobOpening.objects.filter(is_active=True).order_by('-posted_at')
    serializer_class = JobOpeningSerializer
    pagination_class = None

class JobApplicationViewSet(viewsets.ModelViewSet):
    """
    Endpoint for submitting job applications.
    """
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    http_method_names = ['post']

@login_required
def download_resume(request, pk):
    """
    Securely serves the resume file only to staff members.
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized to view this file.")
    
    application = get_object_or_404(JobApplication, pk=pk)
    return FileResponse(application.resume.open(), as_attachment=True, filename=application.resume.name.split('/')[-1])

class InsightViewSet(viewsets.ModelViewSet):
    queryset = Insight.objects.all()
    serializer_class = InsightSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'media_type']
    search_fields = ['title', 'short_description', 'content']
    ordering_fields = ['published_date', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset