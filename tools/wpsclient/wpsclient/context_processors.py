"""Template context every page needs.

`is_admin` is asked for in the page header and wherever a control is shown only
to administrators. Supplying it here rather than from each view keeps the answer
identical everywhere and keeps templates from reproducing the rule as
`user.is_staff or user.is_superuser`, which would then have to be found and
changed if the rule moved.
"""
from . import scope


def roles(request):
    return {"is_admin": scope.is_admin(getattr(request, "user", None))
            if hasattr(request, "user") else False}
