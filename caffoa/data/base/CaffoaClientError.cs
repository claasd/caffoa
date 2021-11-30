using System;
using Microsoft.AspNetCore.Mvc;

namespace {NAMESPACE}
{{
    public abstract class CaffoaClientError : Exception
    {{
        public CaffoaClientError() : base(){{}}
        public CaffoaClientError(string msg) : base(msg){{}}
        public CaffoaClientError(string msg, Exception inner) : base(msg, inner){{}}
        public abstract IActionResult Result {{ get; }}
    }}

    public class CaffoaJsonParseError : CaffoaClientError
    {{
        public CaffoaJsonParseError(string msg) : base("Error during JSON parsing of payload: " + msg){{}}
        public CaffoaJsonParseError(string msg, Exception inner) : base("Error during JSON parsing of payload: " + msg, inner){{}}

        public static CaffoaJsonParseError NoContent()
        {{
            return new CaffoaJsonParseError("no body found");
        }}

        public static CaffoaJsonParseError FromException(Exception err)
        {{
            var inner = err;
            while (inner.InnerException != null)
                inner = inner.InnerException;
            return new CaffoaJsonParseError(inner.GetType().Name + ": " + inner.Message, err);
        }}

        public static Exception WrongContent(string type, object value, string[] allowedValues)
        {{
            var allowedValuesString = string.Join(", ", allowedValues);
            var valueString = value == null ? "<null>" : value.ToString();
            return new CaffoaJsonParseError($"Could not find correct value to parse for discriminator '{{type}}'. Must be one of [{{allowedValuesString}}], not '{{valueString}}'");
        }}
        public override IActionResult Result {{ get => new ContentResult {{Content = Message, StatusCode = 400}}; }}
    }}
}}