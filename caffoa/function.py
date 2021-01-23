from typing import List, Union

from prance import ResolvingParser

from caffoa.converter import parse_type, to_camelcase, TEMPLATE_FOLDER


class EndPoint:
    def __init__(self, name, path, operation, parameters: list, documentation: list, needs_content: bool):
        self.name = name
        self.parameters = parameters
        self.operation = operation
        self.path = path
        self.documentation = documentation
        self.needs_content = needs_content

    def __str__(self):
        return f"{self.operation} {self.path} -> {self.parameters}"


class Parameter:
    def __init__(self, name: str, type: str, desc: str):
        self.desc = desc
        self.type = type
        self.name = name


def create_function_files(endpoints: List[EndPoint], output_path: str, class_name: str = "UserManagement",
                          namespace: str = "UserManagementFunction"):
    print(__file__)
    with open(TEMPLATE_FOLDER + "/FunctionMethod.cs", "r", encoding="utf-8") as f:
        method_template = f.read()
    with open(TEMPLATE_FOLDER + "/FunctionTemplate.cs", "r", encoding="utf-8") as f:
        class_template = f.read()
    with open(TEMPLATE_FOLDER + "/InterfaceMethod.cs", "r", encoding="utf-8") as f:
        interface_method_template = f.read()
    with open(TEMPLATE_FOLDER + "/InterfaceTemplate.cs", "r", encoding="utf-8") as f:
        interface_template = f.read()
    methods = list()
    interface_methods = list()
    for ep in endpoints:
        params_with_names = list()
        params_with_names_for_interface = list()
        param_names = list()
        if ep.needs_content:
            param_names.append("req.Content")
            params_with_names_for_interface.append("HttpContent content")
        for param in ep.parameters:
            params_with_names.append(f"{param.type} {param.name}")
            params_with_names_for_interface.append(f"{param.type} {param.name}")
            param_names.append(param.name)
        params_for_interface = ", ".join(params_with_names_for_interface)
        params_for_function = ", " + params_for_interface if len(params_with_names) > 0 else ""
        param_name_str = ", ".join(param_names)
        methods.append(
            method_template.format(NAME=ep.name, OPERATION=ep.operation, PATH=ep.path, PARAMS=params_for_function,
                                   PARAM_NAMES=param_name_str))
        interface_methods.append(interface_method_template.format(NAME=ep.name, OPERATION=ep.operation, PATH=ep.path,
                                                                  PARAMS=params_for_interface,
                                                                  DOC="\n\t\t/// ".join(ep.documentation)))
    with open(f"{output_path}/{class_name}Function.generated.cs", "w", encoding="utf-8") as f:
        f.write(class_template.format(METHODS="\n\n".join(methods), NAMESPACE=namespace, CLASSNAME=class_name))
    with open(f"{output_path}/I{class_name}Service.generated.cs", "w", encoding="utf-8") as f:
        f.write(interface_template.format(METHODS="\n\n".join(interface_methods), NAMESPACE=namespace,
                                          CLASSNAME=class_name))


def parse_params(params: list) -> list:
    parameters = list()
    for param in params:
        if param['in'].lower() == "path":
            parameters.append(Parameter(param['name'], parse_type(param['schema']), param.get('description')))
    return parameters


def generate_functions(input_file: str, output_path: str, class_name: Union[str, None], namespace: str):
    if class_name is None:
        class_name = namespace
    parser = ResolvingParser(input_file, strict=False)
    endpoints = list()
    for path, options in parser.specification['paths'].items():
        path = str(path).strip('/')
        base_parameters = list()
        if "parameters" in options:
            base_parameters = parse_params(options["parameters"])
        for operation, config in options.items():
            operation = operation.lower()
            if operation in ["parameters"]:
                continue
            if "operationId" not in config:
                raise Warning(f"OperationId is missing for {path}: {operation}")
            operation_id = to_camelcase(config['operationId']) + "Async"
            documentation = [config['description']]
            for response, response_data in config["responses"].items():
                documentation.append(f"{response} -> {response_data['description']}")
            parameters = base_parameters.copy()
            if "parameters" in config:
                parameters.extend(parse_params(config["parameters"]))
            needs_content = "requestBody" in config
            endpoints.append(EndPoint(operation_id, path, operation, parameters, documentation, needs_content))

    create_function_files(endpoints, output_path, class_name, namespace)
