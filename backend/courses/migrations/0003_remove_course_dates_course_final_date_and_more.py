# Generated by Django 5.1.6 on 2025-04-22 01:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_alter_course_course_alter_course_crn_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='dates',
        ),
        migrations.AddField(
            model_name='course',
            name='final_date',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='final_days',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='final_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='final_time',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='meeting_dates',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='meeting_days',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='meeting_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='meeting_time',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
