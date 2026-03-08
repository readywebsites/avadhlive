from django.contrib import admin
from django.db import models
from django import forms
from django.utils.html import mark_safe
from django.utils.html import format_html
from django.urls import reverse
from django_json_widget.widgets import JSONEditorWidget
from .models import Project, ProjectImage, Enquiry, JobOpening, JobApplication, Insight

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 150px;" />')
        return ""
    image_preview.short_description = "Preview"

class ProjectAdminForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'

    def clean_highlights(self):
        highlights = self.cleaned_data.get('highlights')
        if highlights and not isinstance(highlights, (dict, list)):
            raise forms.ValidationError("Highlights must be a valid JSON object (dictionary) or array (list).")
        return highlights

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = ('title', 'thumbnail_preview', 'category', 'status', 'city', 'location', 'area', 'project_type', 'bhk', 'is_completed', 'show_badge', 'nav_order', 'show_in_nav')
    list_filter = ('category', 'status', 'show_in_nav', 'is_completed', 'show_badge')
    search_fields = ('title', 'city', 'location')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline]
    readonly_fields = ('thumbnail_preview',)

    # This overrides the default text area for all JSONFields in this model
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    # Add it to list_editable to toggle it directly from the list view!
    list_editable = ('is_completed', 'show_badge')

    def thumbnail_preview(self, obj):
        if obj.main_image:
            return mark_safe(f'<img src="{obj.main_image.url}" style="max-height: 50px; max-width: 100px;" />')
        return ""
    thumbnail_preview.short_description = "Image"

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'project_of_interest', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('name', 'email', 'project_of_interest')

@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'location', 'experience', 'is_active', 'posted_at')
    list_filter = ('is_active', 'department', 'location')
    search_fields = ('title', 'description')
    list_editable = ('is_active',)

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate_name', 'email', 'phone', 'job', 'download_resume_link', 'applied_at')
    list_filter = ('job', 'applied_at')
    search_fields = ('candidate_name', 'email', 'phone')
    readonly_fields = ('applied_at',)

    def download_resume_link(self, obj):
        if obj.resume:
            url = reverse('download_resume', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Download Resume</a>', url)
        return "No Resume"
    download_resume_link.short_description = "Resume"

@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'published_date', 'media_type', 'display_size')
    list_filter = ('category', 'published_date', 'media_type')
    search_fields = ('title', 'short_description')
    prepopulated_fields = {'slug': ('title',)}
