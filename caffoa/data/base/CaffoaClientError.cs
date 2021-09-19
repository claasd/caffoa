using System;
using Microsoft.AspNetCore.Mvc;

namespace {NAMESPACE}
{{
    public abstract class CaffoaClientError : Exception
    {{
        public CaffoaClientError() : base(){{}}
        public CaffoaClientError(string msg) : base(msg){{}}
        public abstract IActionResult Result {{ get; }}
    }}

    public class CaffoaJsonParseError : CaffoaClientError
    {{
        public CaffoaJsonParseError(string msg) : base("Error during JSON parsing of payload: " + msg){{}}

        public static CaffoaJsonParseError NoContent()
        {{
            return new CaffoaJsonParseError("no body found");
        }}

        public static CaffoaJsonParseError FromException(Exception err)
        {{
            return new CaffoaJsonParseError(err.GetType().Name + ": " + err.Message);
        }}
        public override IActionResult Result {{ get => new ContentResult {{Content = Message, StatusCode = 400}}; }}
    }}
}}