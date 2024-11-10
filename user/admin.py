from django.contrib.auth.admin import UserAdmin, admin

from .models import User
from rest_framework.authtoken.models import Token

admin.site.register(Token)

@admin.register(User)
class UserAdminCustom(UserAdmin):
    readonly_fields = ('jwt_token', 'projects_created')
    
    list_display = ['username', 'first_name', 'last_name', ]
    
    fieldsets = UserAdmin.fieldsets + (
        ('Информация', {'fields': (
            'jwt_token', 'phone_number', 'projects_availables', 'projects_created')}),
    )

    