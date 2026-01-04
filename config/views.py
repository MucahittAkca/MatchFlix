from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def api_root(request):
    """Matchflix API Root"""
    return Response({
        'message': 'Matchflix API - Film Öneri ve Sosyal Platform',
        'version': 'v1',
        'endpoints': {
            'movies': request.build_absolute_uri('/api/movies/'),
            'swagger': request.build_absolute_uri('/api/schema/swagger/'),
            'admin': request.build_absolute_uri('/admin/'),
        }
    })

