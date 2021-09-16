using Newtonsoft.Json;
{IMPORTS}
namespace {NAMESPACE} {{
    {DESCRIPTION}[JsonObject(MemberSerialization.OptIn)]
    public partial class {NAME}{PARENTS} {{
        public const string {NAME}ObjectName = "{RAWNAME}";
{PROPERTIES}

        public {NAME} To{NAME}() {{
            var item = new {NAME}();
            item.UpdateWith{NAME}(this);
            return item;
        }}

        public void UpdateWith{NAME}({NAME} other) {{
            {BASE_UPDATEPROPS}{UPDATEPROPS}
        }}
    }}
}}
