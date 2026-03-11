import django_filters
from .models import Project
import re
from django.db.models import Q

class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """
    Custom filter for handling comma-separated values for a field,
    enabling multi-select functionality from the frontend.
    """
    pass

class BhkFilter(django_filters.Filter):
    """
    Custom filter for the 'bhk' field that handles both simple text search
    (for residential BHKs) and numeric range filtering (for commercial Sq.Ft.).
    """
    def filter(self, qs, value):
        if not value:
            return qs

        values = [v.strip() for v in value.split(',') if v.strip()]
        
        # Determine if we are filtering by BHK or Sq.Ft. based on the filter values.
        is_bhk_filter = any("BHK" in v.upper() for v in values)
        is_sqft_filter = any("SQ.FT." in v.upper() for v in values)

        if is_bhk_filter:
            bhk_q = Q()
            for bhk_val in values:
                bhk_q |= Q(bhk__icontains=bhk_val)
            return qs.filter(bhk_q).distinct()

        if is_sqft_filter:
            range_q = Q()
            for r_str in values:
                numbers = [int(n) for n in re.findall(r'\d+', r_str)]
                if not numbers:
                    continue
                
                r_min = numbers[0]
                r_max = numbers[1] if len(numbers) > 1 else float('inf')

                # Database query for overlapping ranges: (StartA <= EndB) and (EndA >= StartB)
                # This finds projects where the project's area range overlaps with the filter's area range.
                range_q |= (
                    Q(area_sqft_min__lte=r_max) & 
                    Q(area_sqft_max__gte=r_min)
                )
            
            return qs.filter(range_q).distinct() if range_q else qs

        return qs.filter(bhk__icontains=value)

class ProjectFilter(django_filters.FilterSet):
    city = CharInFilter(field_name='city', lookup_expr='in')
    area = CharInFilter(field_name='area', lookup_expr='in')
    project_type = CharInFilter(field_name='project_type', lookup_expr='in')
    bhk = BhkFilter()

    class Meta:
        model = Project
        fields = ['category', 'status']