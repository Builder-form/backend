# Generated by Django 4.2.4 on 2024-08-21 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('builder_form', '0006_questioninstance_qid_alter_questioninstance_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='created',
            field=models.DateTimeField(default='2012-09-04 06:00', editable=False, verbose_name='last_edit'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='last_edit',
            field=models.DateTimeField(default='2012-09-04 06:00', verbose_name='last_edit'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='answer',
            name='conditions',
            field=models.TextField(default='{"params": "", "conditions":"", "insertion": "Left"}', max_length=10000, verbose_name='conditions'),
        ),
        migrations.AlterField(
            model_name='answer',
            name='next_id',
            field=models.CharField(max_length=50, verbose_name='next id'),
        ),
        migrations.AlterField(
            model_name='project',
            name='questions_queue',
            field=models.CharField(blank=True, default='', max_length=1000, verbose_name='Questions queue'),
        ),
    ]