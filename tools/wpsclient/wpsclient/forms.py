from django import forms

from .models import ServerCSV
from .models import ServerWCS
from .models import ServerWFS
from .models import ServerWPS
from .models import ServerElement

from .models import WaterYieldModel

from .models import Job

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


class JobForm(forms.ModelForm):

    class Meta:
        model = Job
        fields = ('args',)

    def __init__(self, *args, **kwargs):
        try:
            default = kwargs.pop("default")
        except KeyError:
            default = "{}"

        super(JobForm, self).__init__(*args, **kwargs)

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


class JobDynamic(forms.ModelForm):
    class Meta:
        model = Job
        fields = ()
        
    def __init__(self, *args, **kwargs):
        wps_input_fields = kwargs.pop("wps_input_fields")
        super(JobDynamic, self).__init__(*args, **kwargs)

        for i, f in enumerate(wps_input_fields):
            self.fields[f[0]] = forms.CharField(label=f[1])

    def wps_input_data(self):
        for name, value in self.cleaned_data.items():
            yield (self.fields[name].label, value)
        

class WaterYieldForm(forms.ModelForm):
    class Meta:
        model = WaterYieldModel
        fields = ("precipitation_uri",
                  "eto_uri",
                  "depth_to_root_rest_layer_uri",
                  "pawc_uri",
                  "lulc_uri",
                  "watersheds_uri",
                  "biophysical_table_uri",
                  "seasonality_constant")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

##        self.fields["depth"].queryset = ServerElement.objects.filter(server__server_type="WCS")
##        self.fields["precipitation"].queryset = ServerElement.objects.filter(server__server_type="WCS")
##        self.fields["pawc"].queryset = ServerElement.objects.filter(server__server_type="WCS")
##        self.fields["evapotranspiration"].queryset = ServerElement.objects.filter(server__server_type="WCS")
##        self.fields["lulc"].queryset = ServerElement.objects.filter(server__server_type="WCS")
##        self.fields["watersheds"].queryset = ServerElement.objects.filter(server__server_type="WFS")
##        self.fields["biophysical"].queryset = ServerElement.objects.filter(server__server_type="CSV")
