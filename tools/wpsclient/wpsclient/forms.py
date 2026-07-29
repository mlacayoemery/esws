import re

from django import forms

from .models import ElementCSV
from .models import ElementWCS
from .models import ElementWFS
from .models import ServerCSV
from .models import ServerWCS
from .models import ServerWFS
from .models import ServerWPS
from .models import ServerTemplate
from .models import ServerElement

from .models import Job

from .widgets import SplitJSONWidget

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


class ServerFormTemplate(forms.ModelForm):

    class Meta:
        model = ServerTemplate
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


_INVEST_TRAILER = re.compile(r"\[invest:([^\]]*)\]")


def parse_input_metadata(parameter):
    """Split a DescribeProcess abstract into (prose, {key: value}).

    The WPS publishes the InVEST type of each input as a trailer on the
    abstract -- ``[invest:type=raster invest:required=...]`` -- because pywps
    drops ows:Metadata from LiteralInput. Strip it back off for display.
    """
    abstract = parameter.abstract or ""
    meta = {}
    match = _INVEST_TRAILER.search(abstract)
    if match:
        for token in ("invest:" + match.group(1)).split():
            key, _sep, value = token.partition("=")
            if value:
                meta[key.replace("invest:", "")] = value
        abstract = _INVEST_TRAILER.sub("", abstract).strip()
    return abstract, meta


class ProcessForm(forms.Form):
    """A form generated from a WPS DescribeProcess response.

    This is the generalisation of the hand-built water yield form: an input
    that wants spatial data becomes a dropdown of registered sources of the
    matching OWS type, and scalars become typed fields -- rather than one
    free-text JSON blob for the whole process.

    The mapping from InVEST type to element type is the same one the water
    yield form encoded by hand in its ForeignKeys: rasters come from WCS,
    vectors from WFS, tables over plain HTTP.
    """

    ELEMENT_SOURCES = {
        "raster": ElementWCS,
        "singleband_raster": ElementWCS,
        "raster_or_vector": ElementWCS,
        "vector": ElementWFS,
        "csv": ElementCSV,
        "file": ElementCSV,
    }

    def __init__(self, *args, **kwargs):
        parameters = kwargs.pop("parameters")
        super().__init__(*args, **kwargs)

        # Remembered so the view can turn a chosen element back into an OWS
        # URL, and so it knows which fields are element references at all.
        self.element_fields = {}

        for parameter in parameters:
            abstract, meta = parse_input_metadata(parameter)
            invest_type = meta.get("type", "")
            identifier = parameter.identifier

            common = {
                "label": parameter.title or identifier,
                "help_text": abstract,
                # A conditional input is not required up front: whether it
                # applies depends on the values of other inputs.
                "required": str(getattr(parameter, "minOccurs", 0)) not in ("0", "None"),
            }

            source = self.ELEMENT_SOURCES.get(invest_type)
            if source is not None:
                self.fields[identifier] = forms.ModelChoiceField(
                    queryset=source.objects.all().order_by("identifier"),
                    empty_label="---------", **common)
                self.element_fields[identifier] = invest_type
            elif invest_type in ("number", "ratio", "percent"):
                self.fields[identifier] = forms.FloatField(**common)
            elif invest_type == "integer":
                self.fields[identifier] = forms.IntegerField(**common)
            elif invest_type == "boolean":
                common["required"] = False
                self.fields[identifier] = forms.BooleanField(**common)
            elif getattr(parameter, "allowedValues", None):
                choices = [(str(v), str(v)) for v in parameter.allowedValues]
                self.fields[identifier] = forms.ChoiceField(choices=choices, **common)
            else:
                self.fields[identifier] = forms.CharField(**common)


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
        

