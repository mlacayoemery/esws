import pywps

class WebProcess(pywps.Process):
    def __init__(self):
        inputs = [pywps.LiteralInput('message',
                                     'Input message',
                                     data_type='string')]

        outputs = [pywps.LiteralOutput('response',
                                       'Output response',
                                       data_type='string')]

        super(WebProcess, self).__init__(
            self._handler,
            identifier='swat',
            title='SWAT',
            abstract='SWAT rev 664',
            version='664',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        response.outputs['response'].data = request.inputs['message'][0].data
        response.outputs['response'].uom = pywps.UOM('unity')
        return response
