        // constant values for "{NAMELOWER}"
        {ENUMS}

        /// <summary>
        /// immutable array containing all allowed values for "{NAMELOWER}"
        /// </summary>
        public readonly ImmutableArray<{TYPE}> {ENUM_LIST_NAME} = ImmutableArray.Create({ENUM_NAMES});

        [JsonIgnore]
        private {TYPE} _{NAMELOWER}{DEFAULT};

        {DESCRIPTION}{JSON_EXTRA}[JsonProperty("{NAMELOWER}"{JSON_PROPERTY_EXTRA})]
        public virtual {TYPE} {NAMEUPPER} {{
            get {{
                return _{NAMELOWER};
            }}
            set {{
                if (!{ENUM_LIST_NAME}.Contains(value))
                {{
                    var allowedValues = string.Join(", ", {ENUM_LIST_NAME}.Select(v=>v == null ? "null" : v.ToString()));
                    throw new ArgumentOutOfRangeException("{NAMELOWER}",
                        $"{{value}} is not allowed. Allowed values: [{{allowedValues}}]");
                }}
                _{NAMELOWER} = value;
            }}
        }}