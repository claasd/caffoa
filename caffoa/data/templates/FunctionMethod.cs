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
                var debugInformation = new Dictionary<string,  string>();
                debugInformation["Error"] = e.Message;
                debugInformation["ExecptionType"] = e.GetType().Name;
                debugInformation[""] = e.Message;
                debugInformation["FunctionName"] = "{NAME}";
		        debugInformation["Route"] = "{PATH}";
		        debugInformation["Operation"] = "{OPERATION}";
		        debugInformation["Payload"] = await GetPayloadForExceptionLogging(req);
		        {ADDITIONAL_ERROR_INFOS}
		        log.LogCritical(JsonConvert.SerializeObject(debugInformation));
		        throw;
            }}
        }}