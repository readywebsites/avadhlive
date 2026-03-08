from rest_framework import serializers
from .models import Project, Enquiry, JobOpening, JobApplication, Insight
import json
import re
from urllib.parse import urlparse, parse_qs

# --- Helper Functions (Business logic moved from frontend to backend) ---

def get_embed_url(url):
    """Converts a standard YouTube or Vimeo video URL into an embeddable URL."""
    if not url:
        return ""
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        if not hostname:
            return url

        # YouTube
        if 'youtube.com' in hostname or 'youtu.be' in hostname:
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get('v', [None])[0] or parsed_url.path.split('/')[-1]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"

        # Vimeo
        if 'vimeo.com' in hostname:
            video_id = parsed_url.path.split('/')[-1]
            if video_id:
                return f"https://player.vimeo.com/video/{video_id}"
    except Exception:
        # In a real application, you might want to log this error.
        return url  # Return original URL on error
    return url  # Return original URL if no match

def get_map_src_from_embed(embed_html):
    """Extracts the `src` URL from a full HTML iframe embed code."""
    if not embed_html:
        return ""
    match = re.search(r'src="([^"]+)"', embed_html)
    return match.group(1) if match else ""


# --- Serializers ---

class ProjectSerializer(serializers.ModelSerializer):
    """
    The main project serializer, designed to provide a clean and consistent
    API response for the frontend, reducing the need for data sanitization.
    """
    # --- Consistent, Processed Fields ---
    gallery = serializers.SerializerMethodField()
    badge = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    highlights = serializers.JSONField(required=False)
    video_url = serializers.SerializerMethodField()
    map_url = serializers.SerializerMethodField()

    # --- Human-Readable Choice Fields ---
    category = serializers.CharField(source='get_category_display', read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Project
        # Define all fields the frontend will consume.
        fields = [
            'id',
            'slug',
            'title',
            'location',
            'city',
            'area',
            'project_type',
            'address',
            'description',
            'category',
            'status',
            'badge',
            'tagline',
            'main_image',
            'bhk',
            'is_completed',
            'gallery',
            'highlights',
            'amenities',
            'video_url',
            'map_url',
            'show_brochure_section',
            'show_amenities_section',
            'show_gallery_section',
        ]
        # Note: We are replacing inconsistent fields like 'project_highlights',
        # 'gallery_images', 'map_embed_url' with the clean fields above.

    def get_gallery(self, obj):
        """
        Always returns a list of full image URLs.
        It combines the main_image with all gallery images.
        """
        request = self.context.get('request')
        gallery_urls = []

        if obj.main_image:
            gallery_urls.append(request.build_absolute_uri(obj.main_image.url))

        # This assumes a related name 'gallery_images' on your Project model
        # from a ForeignKey on a GalleryImage model.
        if hasattr(obj, 'gallery_images'):
            for img_obj in obj.gallery_images.all():
                if img_obj.image:
                    url = request.build_absolute_uri(img_obj.image.url)
                    if url not in gallery_urls:  # Avoid duplicates
                        gallery_urls.append(url)

        return gallery_urls

    def get_badge(self, obj):
        """
        Provides a consistent badge text.
        """
        if not obj.show_badge:
            return None
        return obj.badge_text

    def get_amenities(self, obj):
        """
        Ensures amenities are always returned as a list of objects,
        where each object has an 'items' list.
        """
        amenities_data = obj.amenities
        if not amenities_data:
            return []

        if isinstance(amenities_data, str):
            try:
                amenities_data = json.loads(amenities_data)
            except json.JSONDecodeError:
                return []

        if not isinstance(amenities_data, list):
            return []

        # Robustness: Filter out non-dict items and ensure 'items' key exists
        valid_amenities = []
        for category in amenities_data:
            if isinstance(category, dict):
                if 'items' not in category:
                    category['items'] = []
                valid_amenities.append(category)
        return valid_amenities

    def validate_highlights(self, value):
        """Ensure highlights is a valid dictionary."""
        if value is not None and not isinstance(value, dict):
            raise serializers.ValidationError("Highlights must be a valid dictionary.")
        return value

    def get_video_url(self, obj):
        """Processes the raw video URL to return a ready-to-embed URL."""
        url = get_embed_url(getattr(obj, 'video_url', None))

        # Automatically append origin for YouTube videos to fix embedding restrictions
        if url and 'youtube.com' in url:
            request = self.context.get('request')
            if request:
                # Try to get origin from query params or HTTP header
                origin = request.query_params.get('origin') or request.META.get('HTTP_ORIGIN')
                
                if origin:
                    separator = "&" if "?" in url else "?"
                    return f"{url}{separator}origin={origin}"
        return url

    def get_map_url(self, obj):
        """Processes the raw map iframe embed code to return just the src URL."""
        return get_map_src_from_embed(getattr(obj, 'map_embed_url', None))

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        # Defensive logic for highlights (preserving original read behavior)
        highlights_data = getattr(instance, 'highlights', None) or getattr(instance, 'project_highlights', None) or {}
        if isinstance(highlights_data, str):
            try:
                highlights_data = json.loads(highlights_data)
            except (json.JSONDecodeError, TypeError):
                highlights_data = {}
        
        ret['highlights'] = highlights_data if isinstance(highlights_data, (dict, list)) else {}
        return ret

class ProjectListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""
    category = serializers.CharField(source='get_category_display', read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)
    badge = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'slug', 'title', 'location', 'city', 'area', 'project_type', 'category', 'status', 'badge', 'tagline', 'main_image', 'bhk']

    def get_badge(self, obj):
        if not obj.show_badge:
            return None
        return obj.badge_text or obj.get_status_display()

class ProjectMiniSerializer(serializers.ModelSerializer):
    """Minimal serializer for navigation menus."""
    image = serializers.ImageField(source='main_image', read_only=True)
    class Meta:
        model = Project
        fields = ['id', 'title', 'slug', 'nav_order', 'location', 'address', 'image']

class EnquirySerializer(serializers.ModelSerializer):
    """Serializer for handling contact form submissions."""
    class Meta:
        model = Enquiry
        fields = '__all__'

class JobOpeningSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOpening
        fields = '__all__'

class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = '__all__'

class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insight
        fields = '__all__'