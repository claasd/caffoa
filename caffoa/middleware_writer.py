import logging
import os
from typing import List, Optional

from caffoa.model import EndPoint, Response, MethodResult


class TypedMiddlewareWriter:
    def __init__(self, version: int, name: str, namespace: str, target_folder: str, interface_name: str):
        self.version = version
        self.interface_name = interface_name
        self.version = version
        self.target_folder = target_folder
        self.namespace = namespace
        self.wrapper_name = f"{name}Middleware"
        self.interface_name = f"I{name}MiddlewareService"
        self.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data/v{version}")
        self.imports = list()
        with open(self.template_folder + "/MiddlewareInterfaceMethod.cs", "r", encoding="utf-8") as f:
            self.interface_method_template = f.read()
        with open(self.template_folder + "/InterfaceTemplate.cs", "r", encoding="utf-8") as f:
            self.interface_template = f.read()

        with open(self.template_folder + "/MiddlewareMethod.cs", "r", encoding="utf-8") as f:
            self.method_template = f.read()

        with open(self.template_folder + "/MiddlewareTemplate.cs", "r", encoding="utf-8") as f:
            self.middleware_template = f.read()

        with open(self.template_folder + "/ClientErrorTemplate.cs", "r", encoding="utf-8") as f:
            self.client_error_template = f.read()
        with open(self.template_folder + "/CaffoaClientError.cs", "r", encoding="utf-8") as f:
            self.caffoa_error_template = f.read()
        with open(self.template_folder + "/ResultWrapperTemplate.cs", "r", encoding="utf-8") as f:
            self.result_wrapper_template = f.read()

    def write(self, endpoints: List[EndPoint]):
        os.makedirs(self.target_folder, exist_ok=True)
        has_error_handlers = self.write_errors(endpoints)
        has_result_wrappers = self.write_result_wrappers(endpoints)
        self.write_interface(endpoints, has_result_wrappers)
        self.write_middleware(endpoints, has_error_handlers, has_result_wrappers)

    def write_result_wrappers(self, endpoints: List[EndPoint]) -> bool:
        imports_str = "".join([f"using {imp};\n" for imp in self.imports])
        wrappers = list()
        for endpoint in endpoints:
            type = self.get_response_type(endpoint.responses)
            if type.is_simple:
                continue
            wrappers.append(type)
        if len(wrappers) == 0:
            return False
        os.makedirs(self.target_folder + "/Wrappers", exist_ok=True)
        for type in wrappers:
            codes = [f"R{code} = {code}" for code in type.codes]

            file_name = os.path.abspath(f"{self.target_folder}/Wrappers/{type.name}.generated.cs")
            logging.info(f"Writing result wrapper to {file_name}")
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.result_wrapper_template.format(NAMESPACE=self.namespace + ".Wrappers",
                                                            NAME=type.name,
                                                            BASE=type.base,
                                                            CODES=",\n\t\t\t".join(codes),
                                                            IMPORTS=imports_str))
        return True

    def write_errors(self, endpoints: List[EndPoint]):
        error_classes = dict()
        for endpoint in endpoints:
            for response in endpoint.responses:
                if 400 <= response.code < 500:
                    name = response.content
                    if name in error_classes:
                        if error_classes[name] != response.code:
                            raise Warning(
                                "The same response object with different error codes is currently not supported")
                    error_classes[name] = response.code
        imports_str = "".join([f"using {imp};\n" for imp in self.imports])
        if len(error_classes) == 0:
            return False

        os.makedirs(self.target_folder + "/Errors", exist_ok=True)
        file_name = os.path.abspath(f"{self.target_folder}/Errors/CaffoaClientError.generated.cs")
        logging.info(f"Writing Client Error to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.caffoa_error_template.format(NAMESPACE=self.namespace + ".Errors"))

        for name, code in error_classes.items():
            file_name = os.path.abspath(f"{self.target_folder}/Errors/{name}ClientError.generated.cs")
            logging.info(f"Writing Client Error to {file_name}")
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.client_error_template.format(NAMESPACE=self.namespace + ".Errors",
                                                          NAME=name,
                                                          CODE=code,
                                                          IMPORTS=imports_str))
        return True

    def write_middleware(self, endpoints: List[EndPoint], has_error_handlers: bool, has_result_wrappers: bool):
        methods = []
        imports = ["System.Collections.Generic"]
        imports.extend(self.imports)
        if has_error_handlers:
            imports.append(self.namespace + ".Errors")
        if has_result_wrappers:
            imports.append(self.namespace + ".Wrappers")
        imports_str = "".join([f"using {imp};\n" for imp in imports])
        for endpoint in endpoints:
            methods.append(self.format_method(endpoint))
        file_name = os.path.abspath(f"{self.target_folder}/{self.wrapper_name}.generated.cs")
        logging.info(f"Writing Middleware to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.middleware_template.format(METHODS="\n\n".join(methods),
                                                    NAMESPACE=self.namespace,
                                                    IMPORTS=imports_str,
                                                    INTERFACENAME=self.interface_name,
                                                    CLASSNAME=self.wrapper_name))

    def format_method(self, endpoint: EndPoint):
        type = self.get_response_type(endpoint.responses)
        params = [f"{param.type} {param.name}" for param in endpoint.parameters]
        call_params = [param.name for param in endpoint.parameters]
        if endpoint.needs_content and self.version == 1:
            params.append("HttpContent contentPayload")
            call_params.append("contentPayload")
        elif self.version == 2:
            params.append("HttpRequest request")
            call_params.append("request")
        formatted_params = ", ".join(params)
        formatted_call_params = ", ".join(call_params)

        return self.method_template.format(NAME=endpoint.name,
                                           PARAMS=formatted_params,
                                           RESULT=type,
                                           CALL_PARAMS=formatted_call_params,
                                           ELEMENT="element" if type.is_simple else "element.Data",
                                           CODE=type.code if type.is_simple else "(int)element.ResultCode",
                                           DOC="\n\t\t/// ".join(endpoint.documentation))

    def write_interface(self, endpoints: List[EndPoint], has_result_wrappers: bool):
        interfaces = []
        imports = ["System.Collections.Generic"]
        imports.extend(self.imports)
        if has_result_wrappers:
            imports.append(self.namespace + ".Wrappers")
        imports_str = "".join([f"using {imp};\n" for imp in imports])

        for endpoint in endpoints:
            interfaces.append(self.format_template(endpoint))

        file_name = os.path.abspath(f"{self.target_folder}/{self.interface_name}.generated.cs")
        logging.info(f"Writing Middleware Interface to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.interface_template.format(METHODS="\n\n".join(interfaces),
                                                   NAMESPACE=self.namespace,
                                                   IMPORTS=imports_str,
                                                   CLASSNAME=self.interface_name))

    def format_template(self, endpoint: EndPoint):
        type = self.get_response_type(endpoint.responses).name
        params = [f"{param.type} {param.name}" for param in endpoint.parameters]
        if endpoint.needs_content and self.version == 1:
            params.append("HttpContent contentPayload")
        elif self.version == 2:
            params.append("HttpRequest request")
        formatted_params = ", ".join(params)
        return self.interface_method_template.format(NAME=endpoint.name,
                                                     PARAMS=formatted_params,
                                                     RESULT=type,
                                                     DOC="\n\t\t/// ".join(endpoint.documentation))

    def get_response_type(self, responses: List[Response]) -> Optional[MethodResult]:
        type = None
        codes = list()
        for response in responses:
            if 200 <= response.code < 300:
                if type is not None and type != response.content:
                    logging.warning("Returning different objects is not supported")
                    return None
                type = response.content
                codes.append(response.code)
        if type is None:
            return None
        result = MethodResult(type)
        if len(codes) == 1:
            result = MethodResult(type)
            result.code = codes[0]
            return result

        result.name = type + "ResultWrapper"
        result.is_simple = False
        result.codes = codes
        return result
