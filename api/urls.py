from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, NavigationAPIView, EnquiryViewSet, BookVisitAPIView, ProjectFilterMetadataView, JobOpeningViewSet, JobApplicationViewSet, download_resume, InsightViewSet, ContactAPIView

router = DefaultRouter()
router.register(r'property', ProjectViewSet)
router.register(r'enquiries', EnquiryViewSet)
router.register(r'careers', JobOpeningViewSet)
router.register(r'apply', JobApplicationViewSet)
router.register(r'insights', InsightViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('navigation/', NavigationAPIView.as_view(), name='navigation'),
    path('book-visit/', BookVisitAPIView.as_view(), name='book-visit'),
    path('contact/', ContactAPIView.as_view(), name='contact'),
    path('filter-metadata/', ProjectFilterMetadataView.as_view(), name='filter-metadata'),
    path('admin/download-resume/<int:pk>/', download_resume, name='download_resume'),
]