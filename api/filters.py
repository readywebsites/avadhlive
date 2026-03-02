import django_filters
from .models import Project

class ProjectFilter(django_filters.FilterSet):
    class Meta:
        model = Project
        fields = {
            'category': ['exact'],
            'status': ['exact'],
            'city': ['exact', 'icontains'], # Allows exact match or case-insensitive contains
            'area': ['exact'],
            'project_type': ['exact'],
            'bhk': ['icontains'],
        }