        // constant values for "{NAMELOWER}"
        {ENUMS}

        /// <summary>
        /// immutable array containing all allowed values for "{NAMELOWER}"
        /// </summary>
        public static readonly ImmutableArray<{TYPE}> {ENUM_LIST_NAME}
            = new ImmutableArray<{TYPE}>() {{ {ENUM_NAMES} }};

        [JsonIgnore]
        private {TYPE} _{NAMELOWER}{DEFAULT}

        {DESCRIPTION}{JSON_EXTRA}[JsonProperty("{NAMELOWER}"{JSON_PROPERTY_EXTRA})]
        public virtual {TYPE} {NAMEUPPER} {{
            get {{
                return _{NAMELOWER};
            }}
            set {{
                {ENUM_CHECK}
                _{NAMELOWER} = value;
            }}
        }}