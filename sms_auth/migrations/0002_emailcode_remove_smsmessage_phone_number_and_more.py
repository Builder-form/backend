# Generated by Django 4.2.4 on 2024-09-01 20:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import sms_auth.utils


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sms_auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=300, unique=True, verbose_name='Email')),
                ('code', models.PositiveIntegerField(default=sms_auth.utils.random_code)),
                ('valid_to', models.DateTimeField(default=sms_auth.utils.valid_to)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Email code',
                'verbose_name_plural': 'Email codes',
                'ordering': ('created_at',),
            },
        ),
        migrations.RemoveField(
            model_name='smsmessage',
            name='phone_number',
        ),
        migrations.AddField(
            model_name='smsmessage',
            name='email',
            field=models.EmailField(default='email@email.com', max_length=300, verbose_name='Email'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='PhoneCode',
        ),
    ]