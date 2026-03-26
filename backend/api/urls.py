from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, NavigationAPIView, EnquiryViewSet, rasa_chat_proxy

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'enquiries', EnquiryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('navigation/', NavigationAPIView.as_view(), name='navigation'),
    path('chat/', rasa_chat_proxy, name='rasa-chat-proxy'),
]