{IMPORTS}

namespace {NAMESPACE}
{{
    public partial class {NAME}
    {{
        public {BASE} Data {{get; set; }}
        public enum Result {{
            {CODES}
        }}
        public Result ResultCode {{ get; set; }}

        public {NAME}({BASE} element, Result resultCode)
        {{
            Data = element;
            ResultCode = resultCode;
        }}
    }}
}}