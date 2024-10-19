from rest_framework import status
from rest_framework.response import Response





class ResponsesMixin:
    def simple_text_response(self, message=None):
        if message is None:
            message = 'OK'
        data = {"data": message}

        return Response(data, status=status.HTTP_200_OK)

    def success_objects_response(self, data):
        return Response(data, status=status.HTTP_200_OK)

    def delete_response(self):
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def create_object_response(self, data):
        return Response(data=data, status=status.HTTP_201_CREATED)
    
    def error_response(self, error_message):
        error = error_message

        return Response(error, status=status.HTTP_400_BAD_REQUEST)
