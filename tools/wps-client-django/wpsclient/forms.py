from django import forms

from .models import ServerCSV
from .models import ServerWCS
from .models import ServerWFS
from .models import ServerWPS

from .models import ProcessWPS

from splitjson.widgets import SplitJSONWidget

##class ServerForm(forms.ModelForm):
##
##    class Meta:
##        model = WPS_Server
##        fields = ('title', 'url',)

class ServerFormCSV(forms.ModelForm):

    class Meta:
        model = ServerCSV
        fields = ('title', 'url',)

class ServerFormWCS(forms.ModelForm):

    class Meta:
        model = ServerWCS
        fields = ('title', 'url',)

class ServerFormWFS(forms.ModelForm):

    class Meta:
        model = ServerWFS
        fields = ('title', 'url',)

class ServerFormWPS(forms.ModelForm):

    class Meta:
        model = ServerWPS
        fields = ('title', 'url',)


class ProcessWPSForm(forms.ModelForm):

    class Meta:
        model = ProcessWPS
        fields = ('args',)

    def __init__(self, *args, **kwargs):
        try:
            default = kwargs.pop("default")
        except KeyError:
            default = "{}"

        super(ProcessWPSForm, self).__init__(*args, **kwargs)

        self.fields["args"].initial = default
        #self.fields['poll'].queryset = Poll.objects.filter(owner=user)
        #self.fields['question'].widget = forms.Textarea()


class testForm(forms.Form):        
    attrs = {'class': 'special', 'size': '40'}
    data = forms.CharField(widget=SplitJSONWidget(attrs=attrs, debug=True))


##class ProcessFormGenerator(forms.ModelForm):
##
##    class Meta:
##
##        def __init__(self, *args, **kwargs):
##            self.model = WPS_Process
##            self.fields = ('args',)
##            
##            super(Meta, self).__init__(*args, **kwargs)
##
##    def __init__(self, *args, **kwargs):
##        super(ProcessForm, self).__init__(*args, **kwargs)
##
