from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget
from .models import Project, ProjectImage, Enquiry

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'location', 'nav_order', 'show_in_nav')
    list_filter = ('category', 'status', 'show_in_nav')
    search_fields = ('title', 'location')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline]
    
    # This overrides the default text area for all JSONFields in this model
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'project_of_interest', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('name', 'email', 'project_of_interest')