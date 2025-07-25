"""
Simple API status check endpoint
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

@csrf_exempt
def api_status(request):
    """
    API status endpoint to check if the backend is working
    """
    try:
        from users.models import CustomUser
        from projects.models import Project
        from reviews.models import Rating, Review
        from payments.models import Payment
        from contracts.models import Contract
        
        # Count records in main tables
        stats = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': {
                'users': CustomUser.objects.count(),
                'projects': Project.objects.count(),
                'ratings': Rating.objects.count(),
                'reviews': Review.objects.count(),
                'payments': Payment.objects.count(),
                'contracts': Contract.objects.count(),
            },
            'endpoints': {
                'users': '/api/users/',
                'projects': '/api/projects/',
                'ratings': '/api/reviews/ratings/',
                'reviews': '/api/reviews/reviews/',
                'payments': '/api/payments/',
                'contracts': '/api/contracts/',
                'notifications': '/api/notifications/',
                'disputes': '/api/disputes/',
                'chats': '/api/chats/',
            },
            'features': {
                'comprehensive_rating_system': True,
                'project_management': True,
                'payment_processing': True,
                'real_time_chat': True,
                'notifications': True,
                'dispute_resolution': True,
            }
        }
        
        return JsonResponse(stats, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)
