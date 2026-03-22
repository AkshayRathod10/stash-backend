from django.db import connection
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import structlog

logger = structlog.get_logger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    logger.info("health check called", path=request.path)
    checks = {}
    # Database
    try:
        connection.ensure_connection()
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {e}'
    # Cache
    try:
        cache.set('_health', 'ok', 5)
        checks['cache'] = 'ok' if cache.get('_health') == 'ok' else 'miss'
    except Exception as e:
        checks['cache'] = f'error: {e}'

    ok = all(v == 'ok' for v in checks.values())
    return Response(
        {
            'status': 'healthy' if ok else 'degraded',
            'checks': checks
        },
        status=200 if ok else 503)