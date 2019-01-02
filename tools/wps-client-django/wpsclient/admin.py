from django.contrib import admin

# Register your models here.

from .models import ServerCSV
from .models import ServerWCS
from .models import ServerWFS
from .models import ServerWPS

admin.site.register(ServerCSV)
admin.site.register(ServerWCS)
admin.site.register(ServerWFS)
admin.site.register(ServerWPS)
