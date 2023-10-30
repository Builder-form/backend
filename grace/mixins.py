from rest_framework import status
from rest_framework.response import Response
from .models import ErrorLogs
class ResponsesMixin:
    def create_log(self, log, user):
        ErrorLogs.objects.create(
            log=log,
            user=user
        )

    def simple_text_response(self, message=None):
        data = {"message": message}
        return Response(data, status=status.HTTP_200_OK)

    def success_objects_response(self, data):
        return Response(data, status=status.HTTP_200_OK)

    def create_object_response(self, data):
        return Response(data=data, status=status.HTTP_201_CREATED)

    def delete_response(self):
        return Response(status=status.HTTP_204_NO_CONTENT)

    def error_response(self, error_message, user, status=status.HTTP_400_BAD_REQUEST):
        self.create_log(error_message, user)
        return Response(error_message, status=status)

    def error_methon_not_allowed_response(self, error_message, user):
        self.create_log({'message':error_message}, user)

        return Response({'message':error_message}, status=status.HTTP_405_METHOD_NOT_ALLOWED)