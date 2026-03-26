import requests
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Project, Enquiry
from .serializers import ProjectSerializer, EnquirySerializer, ProjectMiniSerializer
from collections import defaultdict


@api_view(['POST'])
@authentication_classes([]) # Add this to bypass session auth and CSRF checks for this public webhook
@permission_classes([AllowAny]) # Adjust permissions later based on your auth setup
def rasa_chat_proxy(request):
    # 1. Get the message and user ID from the React frontend
    user_message = request.data.get('message')
    
    # You can use the logged-in user's ID if available, otherwise use a session ID or default
    user_id = request.data.get('sender', 'default_user') 

    if not user_message:
        return Response({"error": "Message text is required."}, status=400)

    # 2. Rasa REST webhook URL (make sure Rasa is running on port 5005)
    rasa_url = "http://localhost:5005/webhooks/rest/webhook"
    
    try:
        # 3. Forward the message to Rasa
        rasa_response = requests.post(rasa_url, json={
            "sender": user_id,
            "message": user_message
        })
        
        # Rasa returns a list of dictionaries (e.g., [{"recipient_id": "default_user", "text": "Hey! How are you?"}])
        bot_replies = rasa_response.json()
        
        # 4. Return the bot's replies back to React
        return Response(bot_replies)
        
    except requests.exceptions.RequestException as e:
        # Handle cases where the Rasa server is not running
        return Response({"error": "Chatbot is currently unavailable. Please try again later."}, status=503)
    
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'slug'
    filterset_fields = ['category', 'status', 'location']

class NavigationAPIView(APIView):
    """
    A custom API view to provide a structured JSON response for the website's navigation.
    This is designed to be the single source of truth, replacing the frontend's `navData.js`.
    """
    def get(self, request, *args, **kwargs):
        # 1. Fetch all relevant projects in a single, efficient query.
        projects = Project.objects.filter(
            category__in=['RESIDENTIAL', 'COMMERCIAL', 'CLUB'],
            show_in_nav=True
        ).order_by('nav_order', 'title')

        # 2. Group projects dynamically by category and status.
        grouped_projects = defaultdict(lambda: defaultdict(list))
        for p in projects:
            grouped_projects[p.category][p.status].append(p)

        # 3. Serialize the grouped data.
        # We pass context={'request': request} so that ImageFields return absolute URLs
        serializer_context = {'request': request}

        res_ongoing_data = ProjectMiniSerializer(grouped_projects.get('RESIDENTIAL', {}).get('ONGOING', []), many=True, context=serializer_context).data
        res_completed_data = ProjectMiniSerializer(grouped_projects.get('RESIDENTIAL', {}).get('COMPLETED', []), many=True, context=serializer_context).data
        com_ongoing_data = ProjectMiniSerializer(grouped_projects.get('COMMERCIAL', {}).get('ONGOING', []), many=True, context=serializer_context).data
        com_completed_data = ProjectMiniSerializer(grouped_projects.get('COMMERCIAL', {}).get('COMPLETED', []), many=True, context=serializer_context).data

        # For clubs, we can combine all statuses into one list.
        # Flatten all statuses for CLUB category to include OPERATIONAL, UPCOMING, etc.
        club_projects_map = grouped_projects.get('CLUB', {})
        club_projects_list = [p for sublist in club_projects_map.values() for p in sublist]
        club_data = ProjectMiniSerializer(club_projects_list, many=True, context=serializer_context).data

        # 4. Construct the final data structure, matching the frontend's `navData.js`
        nav_data = [
            {'id': 'home', 'chapter': 1, 'label': 'Home'},
            {'id': 'about-us', 'chapter': 2, 'label': 'About Us'},
            {
                'id': 'residential',
                'chapter': 3,
                'label': 'Residential',
                'submenu': [
                    {
                        'id': 'res-ongoing',
                        'title': 'On-going Projects',
                        'projects': res_ongoing_data,
                        'viewAll': {'label': 'View All Residential', 'link': '/portfolio/residential'}
                    },
                    {
                        'id': 'res-completed',
                        'title': 'Completed Projects',
                        'projects': res_completed_data,
                        'viewAll': {'label': 'View All Completed', 'link': '/portfolio/residential'}
                    }
                ]
            },
            {
                'id': 'commercial',
                'chapter': 4,
                'label': 'Commercial',
                'submenu': [
                    {
                        'id': 'com-ongoing',
                        'title': 'On-going Projects',
                        'projects': com_ongoing_data,
                        'viewAll': {'label': 'View All Commercial', 'link': '/portfolio/commercial'}
                    },
                    {
                        'id': 'com-completed',
                        'title': 'Completed Projects',
                        'projects': com_completed_data,
                        'viewAll': {'label': 'View All Completed', 'link': '/portfolio/commercial'}
                    }
                ]
            },
            {
                'id': 'club',
                'chapter': 5,
                'label': 'Lifestyle Club',
                'submenu': [{
                    'id': 'club-projects-section',
                    'title': 'Exclusive Clubs',
                    'projects': club_data,
                    'viewAll': {'label': 'View All', 'link': '/portfolio/club'}
                }]
            },
            {'id': 'BLOG', 'chapter': 7, 'label': 'BLOG'},
            # The 'More' section can also be made dynamic with another model if needed.
            {
                'id': 'more', 'chapter': None, 'label': 'More', 'submenu': [
                    {'id': 'more-media', 'title': 'Media', 'link': '/media', 'isSimpleLink': True},
                    {'id': 'more-contact', 'title': 'Contact Us', 'link': '/contact', 'isSimpleLink': True},
                    {'id': 'more-careers', 'title': 'Careers', 'link': '/careers', 'isSimpleLink': True},
                ]
            },
        ]

        return Response(nav_data)

class EnquiryViewSet(viewsets.ModelViewSet):
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySerializer