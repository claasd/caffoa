import logging
import os
from typing import List

from caffoa import duplication_handler
from caffoa.base_writer import BaseWriter
from caffoa.body_type_filter import BodyTypeFilter
from caffoa.converter import get_response_type, is_primitive
from caffoa.model import EndPoint, Response, MethodResult


class FunctionWriter(BaseWriter):
    def __init__(self, version: int, name: str, namespace: str, target_folder: str, interface_name: str):
        super().__init__(version)
        self.interface_name = interface_name
        self.version = version
        self.target_folder = target_folder
        self.namespace = namespace
        self.boilerplate = "{BASE}"
        self.use_factory = True if version >= 3 else False
        self.json_error_handling = {"class": "CaffoaJsonParseError"}
        self.functions_name = f"{name}Functions"
        self.error_folder = os.path.join(target_folder, "Errors")
        self.error_namespace = namespace + ".Errors"
        self.request_body_filter = list()
        self.imports = list()
        self.route_prefix = ''
        self.method_template = self.load_template("FunctionMethod.cs")
        self.class_template = self.load_template("FunctionTemplate.cs")
        self.caffoa_error_template = self.load_template("CaffoaClientError.cs")
        self.client_error_template = self.load_template("ClientErrorTemplate.cs")
        self.generic_client_error_template = self.load_template("GenericClientErrorTemplate.cs")

    def write(self, endpoints: List[EndPoint]):
        os.makedirs(self.target_folder, exist_ok=True)
        imports = []
        imports.extend(self.imports)
        if self.version > 2:
            self.write_errors(endpoints)
            imports.append(self.error_namespace)
            json_error_namespace = self.json_error_handling.get("namespace", self.error_namespace)
            if json_error_namespace not in imports:
                imports.append(json_error_namespace)

        json_error_class = self.json_error_handling["class"]
        function_endpoints = []
        for ep in endpoints:
            function_endpoints.append(self.format_endpoint(ep))
#            imports.extend(BodyTypeFilter(self.request_body_filter).additional_imports(ep))
        interface_name = self.interface_name + "Factory" if self.version > 1 and self.use_factory else self.interface_name
        imports = [f"using {x};\n" for x in imports]
        file_name = os.path.abspath(f"{self.target_folder}/{self.functions_name}.generated.cs")
        logging.info(f"Writing Functions to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.class_template.format(METHODS="\n\n".join(function_endpoints),
                                               NAMESPACE=self.namespace,
                                               CLASSNAME=self.functions_name,
                                               INTERFACENAME=interface_name,
                                               IMPORTS="".join(imports),
                                               JSON_ERROR_CLASS=json_error_class))

    def format_endpoint(self, endpoint: EndPoint) -> str:
        if self.version == 1:
            template_params = self.v1_params(endpoint)
        if self.version == 2:
            template_params = self.v2_params(endpoint)
        if self.version == 3:
            template_params = self.v3_params(endpoint)
        template_params["PARAMS"] = ", ".join(template_params["PARAMS"])
        if len(template_params["PARAM_NAMES"]) > 0:
            template_params["PARAM_NAMES"] = ", " + (", ".join(template_params["PARAM_NAMES"]))
        else:
            template_params["PARAM_NAMES"] = ""
        template_params["CALL"] = template_params["CALL"].format_map(template_params)
        return self.method_template.format_map(template_params)

    def v1_params(self, endpoint: EndPoint) -> dict:
        template_params = self.default_params(endpoint)
        if endpoint.needs_content:
            template_params['PARAMS'].append("req.Content")
        params = ", ".join(template_params["PARAMS"])
        function_call = f"{endpoint.name}({params})"
        default_call = f"return await Service(req, log).{function_call};"
        template_params["INVOCATION"] = self.boilerplate.replace("{BASE}", default_call) \
            .replace("{CALL}", function_call) \
            .replace("\n", "\n\t\t\t\t").strip()
        return template_params

    def v2_params(self, endpoint: EndPoint) -> dict:
        template_params = self.default_params(endpoint)
        if self.use_factory:
            func_invocation = ".Instance(request)"
            if endpoint.needs_content:
                template_params['PARAMS'].append("request.Body")
        else:
            func_invocation = ""
            template_params['PARAMS'].append("request")
        params = ", ".join(template_params["PARAMS"])
        function_call = f"{endpoint.name}({params})"
        default_call = f"return await _service{func_invocation}.{function_call};"
        template_params["INVOCATION"] = self.boilerplate.replace("{BASE}", default_call) \
            .replace("{CALL}", function_call) \
            .replace("\n", "\n\t\t\t\t").strip()
        return template_params

    def v3_params(self, endpoint: EndPoint) -> dict:
        params = self.default_params(endpoint)
        type = get_response_type(endpoint)
        params['VALUE'] = f"var result = "
        filtered_body = BodyTypeFilter(self.request_body_filter).body_type(endpoint)

        if type is None:
            params['RESULT'] = "result"
        elif type.name is None and type.is_simple:
            params['RESULT'] = f"new StatusCodeResult({type.code})"
            params['VALUE'] = ""
        elif type.name is None:
            params['RESULT'] = f"new StatusCodeResult(result)"
        elif type.is_simple:
            result = self.get_result_handler(type)
            params['RESULT'] = f"new JsonResult({result}) {{StatusCode = {type.code}}}"
        elif type.base is None:
            params['RESULT'] = "new StatusCodeResult(code)"
            params['VALUE'] = "var code = "
        else:
            params['RESULT'] = f"new JsonResult(result) {{StatusCode = code}}"
            params['VALUE'] = f"var (result, code) = "
        error_infos = [f'("{param.name}", {param.name})' for param in
                       endpoint.parameters]
        if len(error_infos) > 0:
            params['ADDITIONAL_ERROR_INFOS'] = ", " + (", ".join(error_infos))
        if self.use_factory:
            params["FACTORY_CALL"] = "Instance(request)."
        if endpoint.needs_content and endpoint.body is not None and endpoint.body.is_selection():
            params = self.v3_params_selection(endpoint, params)
        elif endpoint.needs_content and filtered_body is not None:
            params['PARAMS'].append(f"await ParseJson<{filtered_body}>(request.Body)")
        elif endpoint.needs_content and endpoint.body is not None:
            params['PARAMS'].append(f"await ParseJson<{endpoint.body.types[0]}>(request.Body)")
        elif endpoint.needs_content and self.use_factory:
            params['PARAMS'].append("request.Body")
        if not self.use_factory:
            params['PARAMS'].append("request")

        return params

    def v3_params_selection(self, endpoint: EndPoint, template_params: dict) -> dict:
        params = list(template_params["PARAMS"]).copy()
        call_params = template_params.copy()
        call_params["VALUE"] = ""
        cases = list()
        allowed_values = list()
        for value,typename in endpoint.body.mapping.items():
            option_params = params.copy()
            option_params.append(f"ToObject<{typename}>(jObject)")
            if not self.use_factory:
                option_params.append(f"request")
            call_params["PARAMS"] = ", ".join(option_params)
            call = "await _service.{FACTORY_CALL}{NAME}({PARAMS})".format_map(call_params)
            cases.append(f'"{value}" => {call}')
            allowed_values.append(f'"{value}"')
        template = self.load_template("FunctionSwitchTemplate.cs")
        template_params["CASES"] = ",\n\t\t\t\t\t".join(cases)
        template_params["CASES_ALLOWED_VALUES"] = ", ".join(allowed_values)
        template_params["DISC"] = endpoint.body.discriminator
        template_params["JSON_ERROR_CLASS"] = self.json_error_handling.get("class")
        template_params["CALL"] = template.format_map(template_params)
        return template_params




    def default_params(self, endpoint: EndPoint) -> dict:
        extra_error_info = [f'debugInformation["p_{param.name}"] = {param.name}.ToString();\n\t\t\t\t' for param in
                            endpoint.parameters]
        return dict(
            NAME=endpoint.name,
            OPERATION=endpoint.method,
            PATH=self.route_prefix + endpoint.path,
            PARAMS=[param.name for param in endpoint.parameters],
            PARAM_NAMES=[f"{param.type} {param.name}" for param in endpoint.parameters],
            ADDITIONAL_ERROR_INFOS="".join(extra_error_info),
            INVOCATION="",
            RESULT="",
            VALUE="",
            FACTORY_CALL="",
            CALL="{VALUE}await _service.{FACTORY_CALL}{NAME}({PARAMS});"
        )

    def write_errors(self, endpoints: List[EndPoint]):
        error_classes = dict()
        generic_error_classes = dict()
        for endpoint in endpoints:
            if endpoint.responses is None:
                continue
            for response in endpoint.responses:
                if 400 <= response.code < 500:
                    name = response.content
                    if name is None:
                        generic_error_classes[f'Generic{response.code}'] = response.code
                        continue
                    if name in error_classes:
                        if error_classes[name] != response.code:
                            raise Warning(
                                "The same response object with different error codes is currently not supported")
                    error_classes[name] = response.code

        imports_str = "".join([f"using {imp};\n" for imp in self.imports])
        os.makedirs(self.error_folder, exist_ok=True)
        file_name = os.path.abspath(f"{self.error_folder}/CaffoaClientError.generated.cs")
        logging.info(f"Writing Client Error to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.caffoa_error_template.format(NAMESPACE=self.error_namespace))

        for name, code in error_classes.items():
            if duplication_handler.should_generate("Error/" + name):
                duplication_handler.store_generated("Error/" + name)
                file_name = os.path.abspath(f"{self.error_folder}/{name}ClientError.generated.cs")
                logging.info(f"Writing Client Error to {file_name}")
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(self.client_error_template.format(NAMESPACE=self.error_namespace,
                                                              NAME=name,
                                                              CODE=code,
                                                              IMPORTS=imports_str))
        for name, code in generic_error_classes.items():
            if duplication_handler.should_generate("Error/" + name):
                duplication_handler.store_generated("Error/" + name)
                file_name = os.path.abspath(f"{self.error_folder}/{name}ClientError.generated.cs")
                logging.info(f"Writing Client Error to {file_name}")
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(self.generic_client_error_template.format(NAMESPACE=self.error_namespace,
                                                                      NAME=name,
                                                                      CODE=code))

    def get_result_handler(self, result: MethodResult):
        return "result"
        base = result.base
        is_array = False
        if base.startswith("IEnumerable<"):
            base = base[12:-1]
            is_array = True
        if is_primitive(base):
            return "result"
        if is_array:
            return f"result.Select(o=>o.To{base}())"
        return f"result.To{result.name}()"


