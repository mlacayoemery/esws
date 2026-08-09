"""Who may see which rows.

Every visibility rule in the dashboard lives here rather than in the 60-odd
views, so that "what can this user see" has one answer that can be read in one
place and tested on its own. A view that filters its own queryset by hand is a
view that can be forgotten when the rules change.

The rules:

  admin       -- sees everything, exactly as the dashboard behaved before there
                 were users at all.
  owner       -- sees what they created.
  public      -- anyone logged in sees a row whose owner marked it public.
  job outputs -- an element produced by a public job is public, without being
                 toggled itself. The edge already exists (ElementProvenance),
                 so this is a join and not a copied flag.
  unowned     -- admin-only. Rows that predate ownership match none of the
                 clauses below, so they fall out of every user query without a
                 special case. That is deliberate: the alternative, treating
                 them as public, would expose one person's history to everyone
                 the moment logins were switched on.
"""
from django.db.models import Q

from .models import Job, Server, ServerElement


def is_admin(user):
    """Admins are Django staff/superusers.

    Kept as a function rather than inlined so there is one definition to change
    if admin ever comes from somewhere else (a group, or an external role
    service) -- the views and templates all ask this question through here.
    """
    return bool(user.is_authenticated and (user.is_staff or user.is_superuser))


def _restrict(queryset, user, extra=None):
    """Owned-by-user OR public, plus any model-specific clause."""
    if is_admin(user):
        return queryset
    if not user.is_authenticated:
        return queryset.none()
    visible = Q(ownership__user=user) | Q(ownership__is_public=True)
    if extra is not None:
        visible |= extra
    # distinct(): the provenance clause joins through a second table, which can
    # repeat a row that matches on more than one branch.
    return queryset.filter(visible).distinct()


def visible_servers(user, queryset=None):
    return _restrict(Server.objects.all() if queryset is None else queryset, user)


def visible_jobs(user, queryset=None):
    return _restrict(Job.objects.all() if queryset is None else queryset, user)


def visible_elements(user, queryset=None):
    """Owned, public, or produced by a public job."""
    return _restrict(
        ServerElement.objects.all() if queryset is None else queryset, user,
        extra=Q(provenance__job__ownership__is_public=True))


def owns(user, instance):
    """True when this user claimed the row. Admins are not owners -- they can
    see and administer everything, but "who made this" stays a fact about the
    user who made it."""
    ownership = getattr(instance, "ownership", None)
    return bool(ownership and user.is_authenticated
                and ownership.user_id == user.pk)


def may_modify(user, instance):
    """Editing, deleting, running, or changing what is public.

    An unowned row is modifiable only by an admin, which matches it being
    visible only to an admin.
    """
    return is_admin(user) or owns(user, instance)


def claim(instance, user, is_public=False):
    """Record who created a row. Idempotent: re-registering something already
    claimed leaves the original owner in place rather than transferring it."""
    from .models import ElementOwner, JobOwner, ServerOwner

    owner_model = {Server: ServerOwner,
                   ServerElement: ElementOwner,
                   Job: JobOwner}[_owned_base(instance)]
    field = {ServerOwner: "server",
             ElementOwner: "element",
             JobOwner: "job"}[owner_model]

    if user is None or not user.is_authenticated:
        return None
    owner, _created = owner_model.objects.get_or_create(
        defaults={"user": user, "is_public": is_public},
        **{field: _owned_base_instance(instance)})
    return owner


def _owned_base(instance):
    """The multi-table parent an ownership row points at.

    ServerCSV and ElementWPS are subclasses; the claim is recorded against
    Server / ServerElement so one row covers the object whichever subclass it is
    read back as.
    """
    for base in (Server, ServerElement, Job):
        if isinstance(instance, base):
            return base
    raise TypeError("not an ownable model: %r" % (instance,))


def _owned_base_instance(instance):
    base = _owned_base(instance)
    if isinstance(instance, base) and type(instance) is not base:
        return base.objects.get(pk=instance.pk)
    return instance
