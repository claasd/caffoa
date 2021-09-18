using Microsoft.AspNetCore.Mvc;

namespace {NAMESPACE}
{{
    public partial class {NAME}ClientError : CaffoaClientError
    {{
        public override IActionResult Result => new StatusCodeResult({CODE});
    }}
}}