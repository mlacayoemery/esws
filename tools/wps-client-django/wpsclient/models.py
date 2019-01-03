from django.db import models
from jsonfield import JSONField

# Create your models here.

##class WPS_Server(models.Model):
##    ows = models.CharField(max_length=3)
##    title = models.CharField(max_length=200)
##    url = models.URLField(max_length=200)
##
##    def publish(self):
##        self.save()
##
##    def __str__(self):
##        return self.title

##class WPS_Process(models.Model):
##    server = models.ForeignKey(WPS_Server, on_delete=models.CASCADE)   
##    identifier = models.CharField(max_length=200)
##
##    args = JSONField()
##
##    def publish(self):
##        self.save()
##
##    def __str__(self):
##        return "-".join([self.server,
##                         self.process])

class Server(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    

    registrations = models.IntegerField(default=0)
    jobs = models.IntegerField(default=0)

    def publish(self):
        self.save()

    def __str__(self):
        return self.title

class ServerCSV(Server):
    server_type = models.CharField(max_length=3, default='CSV', editable=False)

class ServerWCS(Server):
    server_type = models.CharField(max_length=3, default='WCS', editable=False)

class ServerWFS(Server):
    server_type = models.CharField(max_length=3, default='WFS', editable=False)

class ServerWPS(Server):
    server_type = models.CharField(max_length=3, default='WPS', editable=False)

class ServerElement(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE)   
    identifier = models.CharField(max_length=200)

    def publish(self):
        self.save()

    def __str__(self):
        return "-".join([self.server,
                         self.identifier])


class Job(models.Model):
    server = models.ForeignKey(ServerWPS, on_delete=models.CASCADE)   
    identifier = models.CharField(max_length=200)

    args = JSONField()

    def publish(self):
        self.save()

    def __str__(self):
        return "-".join([self.server,
                         self.process])

##class WCS_Instance(models.Model):
##    server = models.ForeignKey(WCS_Server, on_delete=models.CASCADE)   
##    identifier = models.CharField(max_length=200)
##
##    def publish(self):
##        self.save()
##
##    def __str__(self):
##        return "-".join([self.server,
##                         self.process])
##

##class ModelGenerator(models.Model):
##    def __init__(self, *args, **kwargs):
##        super(ProcessForm, self).__init__(*args, **kwargs)
##
##        server = models.ForeignKey(WPS_Server)   
##        identifier = models.CharField(max_length=200)
##
##        args = JSONField()
##        
