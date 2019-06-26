from django.db import models

# Create your models here.

import datetime
from django.utils import timezone

class Project(models.Model):
    project_name = models.CharField(max_length=200)
    comments = models.CharField(max_length=4000)
    state = models.CharField(max_length=2)
    par_ver_code = models.CharField(max_length=128)
    create_date = models.DateTimeField('date created')

    class Meta:
        app_label = 'recml'

    def __str__(self):
        return self.project_name

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.create_date <= now

    was_published_recently.admin_order_field = 'create_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Created recently?'

class Flow(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    flow_name = models.CharField(max_length=200)
    exec_order = models.IntegerField()
    comments = models.CharField(max_length=4000)
    state = models.CharField(max_length=128)

    class Meta:
        app_label = 'recml'

    def __str__(self):
        return self.flow_name