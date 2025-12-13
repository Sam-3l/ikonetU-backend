from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Custom exception handler to format errors consistently
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'message': response.data.get('detail', str(exc))
        }
        
        if isinstance(response.data, dict):
            for key, value in response.data.items():
                if key != 'detail':
                    if isinstance(value, list):
                        custom_response_data['message'] = value[0] if value else str(exc)
                    else:
                        custom_response_data['message'] = value
                    break
        
        response.data = custom_response_data

    return response