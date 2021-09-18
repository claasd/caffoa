using System;
using Microsoft.AspNetCore.Mvc;

namespace {NAMESPACE}
{{
    public abstract class CaffoaClientError : Exception
    {{
        public abstract IActionResult Result {{ get; }}
    }}
}}