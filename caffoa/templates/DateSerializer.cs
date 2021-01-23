using Newtonsoft.Json.Converters;

namespace {NAMESPACE} {{
    class CustomJsonDateConverter : IsoDateTimeConverter
    {{
        public CustomJsonDateConverter()
        {{
            DateTimeFormat = "yyyy-MM-dd";
        }}
    }}
}}
