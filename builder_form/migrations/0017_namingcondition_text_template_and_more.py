# Generated by Django 4.2.4 on 2024-10-20 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('builder_form', '0016_namingcondition'),
    ]

    operations = [
        migrations.AddField(
            model_name='namingcondition',
            name='text_template',
            field=models.CharField(default='', max_length=1000, verbose_name='Text template'),
        ),
        migrations.AlterField(
            model_name='namingcondition',
            name='condition_type',
            field=models.CharField(choices=[('EQUAL', 'Equal'), ('NOT_EQUAL', 'Not Equal'), ('GREATER_THAN', 'Greater Than'), ('LESS_THAN', 'Less Than'), ('IN', 'In'), ('NOT_IN', 'Not In'), ('CONTAINS', 'Contains'), ('NOT_CONTAINS', 'Not Contains'), ('ANSWERED', 'Answered'), ('NOT_ANSWERED', 'Not Answered')], max_length=50, verbose_name='Condition Type'),
        ),
    ]