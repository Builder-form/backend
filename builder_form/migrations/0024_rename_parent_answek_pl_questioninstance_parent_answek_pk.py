# Generated by Django 4.2.4 on 2024-12-14 14:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builder_form', '0023_questioninstance_parent_answek_pl_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='questioninstance',
            old_name='parent_answek_pl',
            new_name='parent_answek_pk',
        ),
    ]