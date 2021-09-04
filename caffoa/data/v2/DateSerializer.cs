using Newtonsoft.Json.Converters;

namespace {NAMESPACE} {{
    /// <summary>
    /// custom converter to create date formats.
    /// By default. Newtonsoft-Json only supports DateTime formats.
    /// </summary>
    public class CustomJsonDateConverter : IsoDateTimeConverter
    {{
        public CustomJsonDateConverter()
        {{
            DateTimeFormat = "yyyy-MM-dd";
        }}
    }}
}}
