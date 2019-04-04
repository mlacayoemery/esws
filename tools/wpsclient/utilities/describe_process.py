import owslib.wps

server_url = "http://127.0.0.1:5000/wps" #PyWPS
process_id = "routedem"

wps = owslib.wps.WebProcessingService(server_url, verbose=False, skip_caps=True)
process = wps.describeprocess(process_id)

process_input = []
for parameter in process.dataInputs:

    if parameter.dataType == "ComplexData":
        for v in parameter.supportedValues:
            print(v.mimeType)

    parameter_details = [parameter.identifier,
                         parameter.title,
                         parameter.abstract,
                         parameter.dataType,
                         parameter.minOccurs,
                         parameter.maxOccurs]

    parameter_details = [v if v != None else "" for v in parameter_details]
    process_input.append(parameter_details)

process_output = []
for parameter in process.processOutputs:

    if parameter.dataType == "ComplexData":
        for v in parameter.supportedValues:
            print(v.mimeType)

    parameter_details = [parameter.identifier,
                         parameter.title,
                         parameter.abstract,
                         parameter.dataType]

    parameter_details = [v if v != None else "" for v in parameter_details]
    process_output.append(parameter_details)
