from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Project
from .serializers import ProjectSerializer
from .filters import ProjectFilter

class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing projects, with support for filtering and searching.
    """
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    lookup_field = 'pk'  # Use pk for detail view, i.e., /api/property/1/

    # Define the filter backends to use
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)

    # For DjangoFilterBackend: specify the filter class from filters.py
    filterset_class = ProjectFilter

    # For SearchFilter: specify which fields to search against with `?search=`
    search_fields = ('name', 'description', 'location')

    # For OrderingFilter: specify which fields can be used for ordering
    ordering_fields = ['name', 'created_at', 'location']

    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        """
        Custom endpoint to get available filter options for the frontend.
        """
        queryset = self.get_queryset()
        locations = sorted(list(queryset.values_list('location', flat=True).distinct()))
        project_types = sorted(list(queryset.values_list('project_type', flat=True).distinct()))
        
        return Response({
            'locations': [loc for loc in locations if loc],
            'types': [ptype for ptype in project_types if ptype],
        })