# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-23 19:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0025_auto_20180608_0114'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipeinputfile',
            old_name='scale_file',
            new_name='input_file',
        ),
    ]
