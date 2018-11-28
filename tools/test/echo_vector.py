import pywps

class WebProcess(pywps.Process):
    def __init__(self):
        inputs = [pywps.ComplexInput('message',
                                     'Input message',
                                     supported_formats=[pywps.Format('application/gml+xml'),
                                                        pywps.Format('text/xml')],
                                     mode=pywps.validator.mode.MODE.NONE)]

        outputs = [pywps.ComplexOutput('response',
                                       'Output response',
                                       supported_formats=[pywps.Format('application/gml+xml')])]

        super(WebProcess, self).__init__(
            self._handler,
            identifier='echo_vector',
            title='Echo Vector Test',
            abstract='Returns the given vector',
            version='1.0.0.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        response.outputs['response'].data = request.inputs['message'][0].data

        return response
