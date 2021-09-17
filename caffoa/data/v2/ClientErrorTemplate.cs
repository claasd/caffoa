using Microsoft.AspNetCore.Mvc;
{IMPORTS}

namespace {NAMESPACE}
{{
    public partial class {NAME}ClientError : CaffoaClientError
    {{
        public {NAME} Element {{ get; set; }} = new {NAME}();
        public override IActionResult Result => new JsonResult(Element) {{StatusCode = {CODE}}};
    }}
}}