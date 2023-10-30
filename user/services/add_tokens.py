from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# for user in User.objects.all():
#     print(user)
#     Token.objects.get_or_create(user=user)
#     user.role = 'customer'
#     user.save()