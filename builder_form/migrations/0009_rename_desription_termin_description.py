# Generated by Django 4.2.4 on 2024-08-30 08:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder_form', '0008_termin_alter_project_created_alter_project_last_edit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='termin',
            old_name='desription',
            new_name='description',
        ),
    ]