import re
from rest_framework import viewsets, filters
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django_filters.rest_framework import DjangoFilterBackend
from .models import Project, Enquiry, JobOpening, JobApplication, Insight
from .serializers import ProjectSerializer, ProjectListSerializer, EnquirySerializer, ProjectMiniSerializer, JobOpeningSerializer, JobApplicationSerializer, InsightSerializer
from .filters import ProjectFilter # <-- Import the new filter
from collections import defaultdict
from django.shortcuts import render

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
            category__in=[Project.Category.RESIDENTIAL, Project.Category.COMMERCIAL, Project.Category.CLUB],
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

        # For clubs, we can combine all statuses into one list.
        # Flatten all statuses for CLUB category to include OPERATIONAL, UPCOMING, etc.
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
                'id': 'club',
                'chapter': 5,
                'label': 'Lifestyle Club',
                'submenu': [{
                    'id': 'club-projects-section',
                    'title': 'Exclusive Clubs',
                    'projects': club_data,
                    'viewAll': {'label': 'View All', 'link': '/portfolio/club'}
                }]
            },
            {'id': 'BLOG', 'chapter': 7, 'label': 'BLOG'},
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

        # 4. Extract Unique BHK Options
        # Since a project might have "2 BHK, 3 BHK", we split and collect unique values
        bhk_raw = queryset.values_list('bhk', flat=True).exclude(bhk__isnull=True).distinct()
        bhk_set = set()
        for s in bhk_raw:
            # Split by common delimiters like '&' or ','
            parts = re.split(r'[&,]', str(s))
            for p in parts:
                clean_val = p.strip()
                if "BHK" in clean_val.upper():
                    bhk_set.add(clean_val)
        
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
                "bhk": sorted(list(bhk_set)),
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