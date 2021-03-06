# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-09-13 16:32
from __future__ import unicode_literals

from django.db import migrations

def get_version_array(version):
    """Constructs a complete Docker image and tag with the correct packageVersion value
    """
    from job.models import JobType

    job_type = JobType()
    return job_type.get_job_version_array(version)

class Migration(migrations.Migration):

    dependencies = [
        ('job', '0047_jobtype_versionarray'),
    ]

    def populate_job_type_version_array(apps, schema_editor):
        # Go through all of the JobType models and populate their version array
        JobType = apps.get_model('job', 'JobType')

        for job_type in JobType.objects.all().iterator():
            job_type.version_array = get_version_array(job_type.version)
            job_type.save()

    operations = [
        migrations.RunPython(populate_job_type_version_array),
    ]
