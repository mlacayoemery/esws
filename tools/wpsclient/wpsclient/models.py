from django.conf import settings
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

    # A holding area rather than a real endpoint: the "Local Pending" sources
    # list a job's anticipated outputs until the run produces them. Excluded
    # from destination pickers, since nothing can be published to them.
    is_pending = models.BooleanField(default=False)

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

class ElementFingerprint(models.Model):
    """What a registered element's data looked like the last time it was checked.

    A registered element points at data on someone else's server and nothing
    announces when that data is replaced, so noticing means recording a
    fingerprint and comparing the next one against it.

    Its own table rather than columns on ServerElement: the wpsclient app has
    migrations disabled (MIGRATION_MODULES) and its tables come from
    `migrate --run-syncdb`, which creates a missing table but cannot add a column
    to one that already exists.
    """

    element = models.OneToOneField(ServerElement, on_delete=models.CASCADE,
                                   related_name="fingerprint")

    # Content hash, computed so that incidental variation does not count as a
    # change -- see tools/data_fingerprint.py. Empty when the last check failed.
    digest = models.CharField(max_length=64, default="")
    # Validators, when the server offers them: they let a check skip the download.
    etag = models.CharField(max_length=200, default="")
    last_modified = models.CharField(max_length=64, default="")
    size = models.BigIntegerField(null=True, blank=True)

    checks = models.IntegerField(default=0)
    checked_at = models.DateTimeField(null=True, blank=True)
    # When the data was last seen to differ from the previous check. Null means it
    # has not changed since it was first fingerprinted.
    changed_at = models.DateTimeField(null=True, blank=True)
    # Set when the last check could not reach the data at all, which is not the
    # same as the data being unchanged.
    unreachable = models.BooleanField(default=False)

    def __str__(self):
        return "%s@%s" % (self.element, self.digest[:12] or "unknown")


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


class ElementProvenance(models.Model):
    """Which job produced a registered element.

    Jobs already form a pipeline: a job's published outputs are registered as
    elements, and any later job can select them as inputs. Nothing recorded the
    link, so the pipeline existed without being visible. This is the missing
    edge.

    One row per element, rewritten when a later run republishes the same name --
    the question it answers is "what made what is there now", not "what has ever
    been there". Its own table rather than a column on ServerElement, for the
    same reason as ElementFingerprint: this app cannot ALTER an existing one.
    """

    element = models.OneToOneField(ServerElement, on_delete=models.CASCADE,
                                   related_name="provenance")
    job = models.ForeignKey(Job, on_delete=models.CASCADE,
                            related_name="produced")
    recorded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s <- job %s" % (self.element.identifier, self.job_id)


class Ownership(models.Model):
    """Who created a row, and whether everyone else may see it.

    Its own table per owned type rather than columns on Server/ServerElement/Job,
    for the same reason as ElementFingerprint and ElementProvenance: this app has
    migrations disabled (MIGRATION_MODULES) and its tables come from
    `migrate --run-syncdb`, which creates a missing table but cannot add a column
    to one that already exists.

    That constraint applies to these tables too, once they exist. A field added
    here later would need yet another table, so the ones below are the fields the
    scoping rules need, decided in one pass:

      user       -- the owner. Deleting the user deletes the claim, which leaves
                    the row unowned, and an unowned row is admin-only.
      is_public  -- opt-in visibility for everyone else. Default False: a row is
                    private unless someone says otherwise, so a new kind of
                    object cannot leak by forgetting to set this.
      created_at -- when it was claimed, not when the row was made.

    Abstract, so each owned type gets its own table with all of these columns
    rather than one shared table keyed by content type: a OneToOneField gives the
    database the uniqueness constraint that "one owner per row" needs, and
    generic relations cannot be filtered across a join the way scoping needs.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "%s (%s)" % (self.user, "public" if self.is_public else "private")


class ServerOwner(Ownership):
    """OneToOne against Server, the multi-table parent, so a claim on a
    ServerCSV/WCS/WFS/WPS/Template is the same row -- the subclasses share the
    parent's primary key, and scoping filters traverse the parent relation."""

    server = models.OneToOneField(Server, on_delete=models.CASCADE,
                                  related_name="ownership")


class ElementOwner(Ownership):
    """OneToOne against ServerElement, the multi-table parent. See ServerOwner.

    An element also inherits visibility from the job that produced it -- see
    ElementProvenance and wpsclient.scope.visible_elements -- so a public job
    exposes its outputs without each one being toggled individually.
    """

    element = models.OneToOneField(ServerElement, on_delete=models.CASCADE,
                                   related_name="ownership")


class JobOwner(Ownership):
    """OneToOne against Job. Setting is_public here also publishes the job's
    outputs, via the ElementProvenance edge rather than by copying the flag onto
    each element: the outputs of a run are not independently owned, and a
    duplicated flag would drift the first time one side was updated alone."""

    job = models.OneToOneField(Job, on_delete=models.CASCADE,
                               related_name="ownership")

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

