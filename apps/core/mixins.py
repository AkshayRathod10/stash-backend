from rest_framework.response import Response

class StandardResponseMixin:
    def success(self, data, status=200):
        return Response({'success': True, 'data': data, 'error': None}, status=status)