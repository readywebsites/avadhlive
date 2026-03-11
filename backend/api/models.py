from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator

def project_directory_path(instance, filename):
    """
    Generates a unique path for project media files.
    Example: MEDIA_ROOT/projects/avadh-riverside/brochure.pdf
    """
    # If the instance is a Project, use its slug.
    # If it's a ProjectImage, access the related project's slug.
    project_slug = instance.slug if hasattr(instance, 'slug') else instance.project.slug
    return f'projects/{project_slug}/{filename}'

class Project(models.Model):
    """
    A single, flexible model to represent all real estate projects.
    """
    # --- Choices for controlled vocabulary ---
    class Category(models.TextChoices):
        RESIDENTIAL = 'RESIDENTIAL', 'Residential'
        COMMERCIAL = 'COMMERCIAL', 'Commercial'
        CLUB = 'CLUB', 'Lifestyle Club'
        INDUSTRIAL = 'INDUSTRIAL', 'Industrial'

    class Status(models.TextChoices):
        ONGOING = 'ONGOING', 'On-going'
        COMPLETED = 'COMPLETED', 'Completed'
        UPCOMING = 'UPCOMING', 'Upcoming'
        OPERATIONAL = 'OPERATIONAL', 'Operational' # For clubs

    # --- Core Project Information ---
    title = models.CharField(max_length=200, unique=True, help_text="The official name of the project.")
    slug = models.SlugField(max_length=220, unique=True, blank=True, help_text="URL-friendly version of the title. Auto-generated.")
    location = models.CharField(max_length=100, help_text="General area, e.g., 'Vesu, Surat'")
    address = models.CharField(max_length=255, help_text="Full address for display and maps.", default="")
    description = models.TextField(help_text="Detailed project description for the showcase page.")

    # --- Categorization and Status ---
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.RESIDENTIAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONGOING)
    badge_text = models.CharField(max_length=50, blank=True, null=True, help_text="Optional text for a custom badge, e.g., 'New Launch', 'Premium', 'Sold Out'.")
    badge_bg_color = models.CharField(max_length=7, default='#eab308', help_text="Hex color code for the badge background.")
    badge_text_color = models.CharField(max_length=7, default='#000000', help_text="Hex color code for the badge text.")

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