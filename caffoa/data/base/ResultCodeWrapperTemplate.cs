{IMPORTS}

namespace {NAMESPACE}
{{
    public partial class {NAME}
    {{
        public enum Result {{
            {CODES}
        }}
        public Result ResultCode {{ get; set; }}

        public {NAME}(Result resultCode)
        {{
            ResultCode = resultCode;
        }}
    }}
}}