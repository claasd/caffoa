        // constant values for "{NAMELOWER}"
        {ENUMS}

        /// <summary>
        /// immutable array containing all allowed values for "{NAMELOWER}"
        /// </summary>
        public static readonly ImmutableArray<{TYPE}> AllowedValuesFor{NAMEUPPER}
            = new ImmutableArray<{TYPE}>() {{ {ENUM_NAMES} }};

        {DESCRIPTION}{JSON_EXTRA}[JsonProperty("{NAMELOWER}"{JSON_PROPERTY_EXTRA})]
        public virtual {TYPE} {NAMEUPPER} {{ get; set; }}{DEFAULT}