from django.contrib.auth import get_user_model

from ..api.exceptions import SMSCodeNotFoundException
from ..conf import conf
from ..models import \
    EmailCode
from ..utils import SmsService

User = get_user_model()


class AuthService(SmsService):
    def __init__(self, email: str, code: str):
        self.email = email
        self.code = code

        super().__init__()

    def process(self):
        generated_code = EmailCode.objects.\
            filter(email=self.email,
                   code=self.code)\
            .first()

        if generated_code is None:
            raise SMSCodeNotFoundException()

        user = generated_code.owner
        is_created = False
        kwargs = {conf.SMS_USER_FIELD: generated_code.email}
        if user is None:
            user, is_created = User.objects.get_or_create(**kwargs,
                                                       defaults={"is_active": True})
        else:
            user.save(**kwargs)

        generated_code.delete()

        return user, is_created
