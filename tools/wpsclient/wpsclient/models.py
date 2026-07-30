from django.db import models

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

class ServerTemplate(ServerWPS):
    """A WPS source whose job forms come prefilled with sample values.

    Points at the same WPS URL as a plain WPS source and lists the same
    processes; the only difference is that job_new preselects the arguments
    recorded in InVEST's sample datastacks, so a process can be run without
    hunting for inputs first.

    Subclasses ServerWPS rather than Server so that Job.server -- a ForeignKey
    to ServerWPS -- accepts a template. The cost is that templates also satisfy
    ServerWPS queries, so the WPS listings exclude them explicitly.

    server_type is inherited, not redeclared: multi-table inheritance forbids
    shadowing a parent field, so it is stamped on save instead.
    """

    def save(self, *args, **kwargs):
        self.server_type = 'TPL'
        return super().save(*args, **kwargs)

class ServerElement(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE)   
    identifier = models.CharField(max_length=200)

    def publish(self):
        self.save()

    def __str__(self):
        return "/".join([str(self.server),
                         self.identifier])


class ElementCSV(ServerElement):
    element_type = models.CharField(max_length=3, default='CSV', editable=False)

class ElementWCS(ServerElement):
    element_type = models.CharField(max_length=3, default='WCS', editable=False)

class ElementWFS(ServerElement):
    element_type = models.CharField(max_length=3, default='WFS', editable=False)

class ElementWPS(ServerElement):
    element_type = models.CharField(max_length=3, default='WPS', editable=False)

class Job(models.Model):
    server = models.ForeignKey(ServerWPS, on_delete=models.CASCADE)   
    identifier = models.CharField(max_length=200)
    status = models.CharField(max_length=12, default='Pending')
    status_url = models.TextField(default="")
    # Where the WPS parks the stored ExecuteResponse for an asynchronous run
    # (statusLocation). Polled to advance `status`; empty for a job that has
    # not been submitted yet.
    status_location = models.TextField(default="")

    args = models.JSONField(default=dict)

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

