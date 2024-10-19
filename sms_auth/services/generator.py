from django.contrib.auth import get_user_model

from ..api.exceptions import \
    SMSWaitException, \
    UserAlreadyExistException

from ..models import EmailCode
from ..utils import SmsService
from ..conf import conf


class GeneratorService(SmsService):
    def __init__(self, email: str, owner=None):
        self.email = email
        self.owner = owner

    def process(self):
        if self.owner is not None:
            code = EmailCode.objects\
                .filter(owner=self.owner)\
                .first()
        else:
            code = EmailCode.objects\
                .filter(email=self.email)\
                .first()

        if code is not None:
            if not code.is_allow:
                raise SMSWaitException()

            code.delete()

        if self.owner is not None:
            kwargs = {conf.SMS_USER_FIELD: self.email}
            if get_user_model().objects.filter(**kwargs).exists():
                raise UserAlreadyExistException()

        EmailCode.objects\
            .create(email=self.email,
                    owner=self.owner)
