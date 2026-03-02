from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, NavigationAPIView, EnquiryViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'enquiries', EnquiryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('navigation/', NavigationAPIView.as_view(), name='navigation'),
]