from typing import Optional

from caffoa.model import EndPoint


class BodyTypeFilter:
    def __init__(self, config: list):
        self.config = config

    def _match_filter(self, endpoint: EndPoint) -> Optional[str]:
        for item in self.config:
            filter = item.get("filter", dict())
            for method in filter.get("methods", list()):
                if method.lower() == endpoint.method:
                    return item["type"]
            for operation in filter.get("operations", list()):
                if operation == endpoint.operation:
                    return item["type"]
        return None

    def body_type(self, endpoint: EndPoint) -> Optional[str]:
        return self._match_filter(endpoint)

    def additional_imports(self, endpoint: EndPoint) -> list:
        type = self._match_filter(endpoint)
        if type is None:
            return list()
        if type.lower() == "jobject":
            return ["Newtonsoft.Json.Linq"]
        return list()
