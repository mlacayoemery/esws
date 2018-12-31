from django.db import models
from jsonfield import JSONField

# Create your models here.

class WPS_Server(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=200)

    def publish(self):
        self.save()

    def __str__(self):
        return self.title

class WPS_Process(models.Model):
    server = models.ForeignKey(WPS_Server, on_delete=models.CASCADE)   
    identifier = models.CharField(max_length=200)

    args = JSONField()

    def publish(self):
        self.save()

    def __str__(self):
        return "-".join([self.server,
                         self.process])


##class ModelGenerator(models.Model):
##    def __init__(self, *args, **kwargs):
##        super(ProcessForm, self).__init__(*args, **kwargs)
##
##        server = models.ForeignKey(WPS_Server)   
##        identifier = models.CharField(max_length=200)
##
##        args = JSONField()
##        
