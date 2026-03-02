from rest_framework import serializers
from .models import Project, Enquiry, ProjectImage

class ProjectMiniSerializer(serializers.ModelSerializer):
    """A lightweight serializer for project previews in the navbar."""
    class Meta:
        model = Project
        fields = ['id', 'title', 'location', 'main_image', 'link']

class ProjectImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImage
        fields = ['id', 'image', 'alt_text']

class ProjectSerializer(serializers.ModelSerializer):
    gallery_images = ProjectImageSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'

class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = '__all__'