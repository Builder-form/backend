# Generated by Django 4.2.4 on 2024-12-14 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('builder_form', '0025_rename_parent_answek_pk_questioninstance_parent_answer_pk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questioninstance',
            name='parent_answer_pk',
            field=models.PositiveIntegerField(blank=True, default=0, max_length=50, null=True, verbose_name='parent_answer_pk'),
        ),
    ]