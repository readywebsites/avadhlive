from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from django_ckeditor_5.fields import CKEditor5Field
from tinymce.models import HTMLField

def project_directory_path(instance, filename):
    """
    Generates a unique path for project media files.
    Example: MEDIA_ROOT/projects/avadh-riverside/brochure.pdf
    """
    # If the instance is a Project, use its slug.
    # If it's a ProjectImage, access the related project's slug.
    project_slug = instance.slug if hasattr(instance, 'slug') else instance.project.slug
    return f'projects/{project_slug}/{filename}'

# Define private storage for sensitive files (like resumes)
private_storage = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'private_media'))

class Project(models.Model):
    """
    A single, flexible model to represent all real estate projects.
    """
    # --- Choices for controlled vocabulary ---
    class Category(models.TextChoices):
        RESIDENTIAL = 'RESIDENTIAL', 'Residential'
        COMMERCIAL = 'COMMERCIAL', 'Commercial'
        CLUB = 'CLUB', 'Lifestyle Club'

    class Status(models.TextChoices):
        ONGOING = 'ONGOING', 'On-going'
        COMPLETED = 'COMPLETED', 'Completed'

    # --- Core Project Information ---
    title = models.CharField(max_length=200, unique=True, help_text="The official name of the project.")
    slug = models.SlugField(max_length=220, unique=True, blank=True, help_text="URL-friendly version of the title. Auto-generated.")
    location = models.CharField(max_length=100, help_text="Display location string, e.g., 'Vesu, Surat'")
    city = models.CharField(max_length=100, blank=True, null=True, help_text="City name for filtering, e.g., 'Surat', 'Vapi'")
    area = models.CharField(max_length=100, blank=True, null=True, help_text="Specific neighborhood, e.g., 'Vesu', 'Dumas', 'Tukvada'")
    project_type = models.CharField(max_length=100, blank=True, null=True, help_text="Type of property, e.g., 'Apartment', 'Villa', 'Office', 'Showroom'")
    bhk = models.CharField(max_length=100, blank=True, null=True, help_text="BHK options for Residential, e.g., '2 BHK, 3 BHK'. Use commas to separate.")
    tagline = models.CharField(max_length=100, blank=True, null=True, help_text="Main highlight for the card (e.g., '3 & 4 BHK Luxury'). Max 100 chars.")
    address = models.CharField(max_length=255, help_text="Full address for display and maps.", default="")
    description = CKEditor5Field('Description', config_name='extends', help_text="Detailed project description for the showcase page.")

    # --- Categorization and Status ---
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.RESIDENTIAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONGOING)
    badge_text = models.CharField(max_length=50, blank=True, null=True, help_text="Optional text for a custom badge, e.g., 'New Launch', 'Premium', 'Sold Out'.")
    show_badge = models.BooleanField(default=True, help_text="Uncheck to hide the badge.")
    badge_bg_color = models.CharField(max_length=7, default='#eab308', help_text="Hex color code for the badge background.")
    badge_text_color = models.CharField(max_length=7, default='#000000', help_text="Hex color code for the badge text.")
    is_completed = models.BooleanField(
        default=False, 
        help_text="Check this box if the project is fully completed. It will show a green 'COMPLETED' stamp on the website."
    )
    
    # --- Flexible Data Fields ---
    highlights = models.JSONField(default=dict, blank=True, help_text="Key-value pairs for project highlights (e.g., {'Configuration': '3 BHK', 'Floors': '14'}).")
    amenities = models.JSONField(default=list, blank=True, help_text="List of amenities strings or a dictionary of categories.")
    show_brochure_section = models.BooleanField(default=True, help_text="Toggle to show/hide the brochure download section.")
    show_amenities_section = models.BooleanField(default=True, help_text="Toggle to show/hide the amenities section.")
    show_gallery_section = models.BooleanField(default=True, help_text="Toggle to show/hide the gallery section.")

    # --- Media and External Links ---
    main_image = models.ImageField(upload_to=project_directory_path, help_text="Primary image shown in project listings and cards.")
    brochure_pdf = models.FileField(
        upload_to=project_directory_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Project e-brochure in PDF format."
    )
    video_url = models.URLField(blank=True, null=True, help_text="Link to a YouTube or Vimeo video for embedding.")
    map_embed_url = models.TextField(blank=True, null=True, help_text="Full embed code from Google Maps (the `<iframe>...</iframe>` part).")

    # --- Navigation & Ordering ---
    show_in_nav = models.BooleanField(default=True, help_text="Uncheck to hide this project from the main navigation dropdowns.")
    nav_order = models.PositiveIntegerField(default=0, help_text="Order in which projects appear in the navigation. Lower numbers appear first.")

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nav_order', 'title'] # Show newest projects first by default
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate the slug from the title if it's not set
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def link(self):
        # This generates the frontend link for the project showcase page
        return f"/property/{self.slug}"

class ProjectImage(models.Model):
    """
    A model to handle the image gallery for a Project.
    """
    project = models.ForeignKey(Project, related_name='gallery_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=project_directory_path, help_text="An image for the project's gallery.")
    alt_text = models.CharField(max_length=100, blank=True, null=True, help_text="Descriptive text for accessibility (screen readers).")

    class Meta:
        ordering = ['id']
        verbose_name = "Project Image"
        verbose_name_plural = "Project Images"

    def __str__(self):
        return f"Image for {self.project.title}"

class Enquiry(models.Model):
    """
    Represents an enquiry made through the website's forms.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    project_of_interest = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Enquiry from {self.name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class JobOpening(models.Model):
    """
    Represents a job opening posted by the admin.
    """
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100, default="Surat")
    experience = models.CharField(max_length=100, help_text="e.g. '2-5 Years'")
    description = CKEditor5Field('Description', config_name='extends')
    is_active = models.BooleanField(default=True)
    posted_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    """
    Represents an application submitted by a candidate.
    """
    job = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name='applications')
    candidate_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    resume = models.FileField(
        upload_to='resumes/',
        storage=private_storage,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc'])]
    )
    cover_letter = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate_name} - {self.job.title}"

class Insight(models.Model):
    """
    A unified model for Blog Posts and Media/Press items.
    """
    CATEGORY_CHOICES = (
        ('blog', 'Blog'),
        ('media', 'Media'),
    )

    SIZE_CHOICES = (
        ('small', 'Small (1x1)'),
        ('large', 'Large (2x2)'),
        ('wide', 'Wide (2x1)'),
        ('tall', 'Tall (1x2)'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='blog')
    
    # Content fields
    image = models.ImageField(upload_to='insights/', blank=True, null=True)
    content = HTMLField(blank=True, null=True, help_text="Main content for Blogs")
    short_description = models.TextField(blank=True, help_text="Excerpt for list view")
    
    # Media specific fields
    media_type = models.CharField(max_length=50, blank=True, help_text="e.g., Award, News, Press")
    external_link = models.URLField(blank=True, null=True, help_text="Link for external media coverage")
    
    # Layout Control
    display_size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='small', help_text="For Media Section Grid")
    flex_grow = models.FloatField(default=1.0, help_text="For Blog Section Masonry (e.g., 1.0, 1.5, 2.0)")
    background_color = models.CharField(max_length=20, blank=True, help_text="Hex code (e.g., #f0f0f0) for Media cards")

    published_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
