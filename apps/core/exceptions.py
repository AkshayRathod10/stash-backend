from rest_framework.views import exception_handler
from rest_framework.response import Response


def _flatten_errors(data):
    """Recursively flatten DRF error dicts into a single string."""
    if isinstance(data, list):
        return ' '.join(_flatten_errors(i) for i in data)
    if isinstance(data, dict):
        return ' '.join(_flatten_errors(v) for v in data.values())
    return str(data)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'success': False,
            'error': {
                'code':    response.status_code,
                'message': _flatten_errors(response.data),
            },
            'data': None,
        }
    return response