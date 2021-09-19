        /// <summary>
        /// auto-generated function invocation.
        ///</summary>
        [FunctionName("{NAME}")]
        public async Task<IActionResult> {NAME}(
            [HttpTrigger(AuthorizationLevel.Function, "{OPERATION}", Route = "{PATH}")]
            HttpRequest request{PARAM_NAMES})
        {{
            try {{
                {INVOCATION}
            }} catch (Exception e) {{
                var debugInformation = new Dictionary<string,  string>();
                debugInformation["Error"] = e.Message;
                debugInformation["ExecptionType"] = e.GetType().Name;
                debugInformation["FunctionName"] = "{NAME}";
		        debugInformation["Route"] = "{PATH}";
		        debugInformation["Operation"] = "{OPERATION}";
		        debugInformation["Payload"] = await GetPayloadForExceptionLogging(req);
		        {ADDITIONAL_ERROR_INFOS}

		        _logger.LogCritical(JsonConvert.SerializeObject(debugInformation));
		        throw;
            }}
        }}