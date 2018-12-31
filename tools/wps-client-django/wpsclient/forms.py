from django import forms

from .models import WPS_Server
from .models import WPS_Process

from splitjson.widgets import SplitJSONWidget

class ServerForm(forms.ModelForm):

    class Meta:
        model = WPS_Server
        fields = ('title', 'url',)

class ProcessForm(forms.ModelForm):

    class Meta:
        model = WPS_Process
        fields = ('args',)

    def __init__(self, *args, **kwargs):
        try:
            default = kwargs.pop("default")
        except KeyError:
            default = "{}"

        super(ProcessForm, self).__init__(*args, **kwargs)

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
