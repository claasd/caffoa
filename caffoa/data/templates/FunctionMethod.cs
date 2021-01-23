        /// <summary>
        /// auto-generated function invocation.
        ///</summary>
        [FunctionName("{NAME}")]
        public static async Task<HttpResponseMessage> {NAME}(
            [HttpTrigger(AuthorizationLevel.Function, "{OPERATION}", Route = "{PATH}")]
            HttpRequestMessage req{PARAMS}, ILogger log)
        {{
            return await Service(req, log).{NAME}({PARAM_NAMES});
        }}