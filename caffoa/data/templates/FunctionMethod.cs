        /// <summary>
        /// auto-generated function invocation.
        ///</summary>
        [FunctionName("{NAME}")]
        public static async Task<HttpResponseMessage> {NAME}(
            [HttpTrigger(AuthorizationLevel.Function, "{OPERATION}", Route = "{PATH}")]
            HttpRequestMessage req{PARAMS}, ILogger log)
        {{
            try {{
                {START_BOILERPLATE}return await Service(req, log).{NAME}({PARAM_NAMES});{END_BOILERPLATE}
            }} catch (Exception e) {{
                var wrappedException =
			        new Exception($"Internal server error in Function '{NAME}': {{e.Message}}", e);
		        wrappedException.Data["FunctionName"] = "{NAME}";
		        wrappedException.Data["Route"] = "{PATH}";
		        wrappedException.Data["Operation"] = "{OPERATION}";
		        {EXCEPTION_PARAMS}throw wrappedException;
            }}
        }}