        /// <summary>
        /// auto-generated function invocation.
        ///</summary>
        [FunctionName("{NAME}")]
        public async Task<IActionResult> {NAME}(
            [HttpTrigger(AuthorizationLevel.Function, "{OPERATION}", Route = "{PATH}")]
            HttpRequest request{PARAM_NAMES})
        {{
            try {{
                {VALUE}await _service.{NAME}({PARAMS});
                return {RESULT};
            }} catch(CaffoaClientError err) {{
                return err.Result;
            }} catch (Exception e) {{
                var debugInformation = new Dictionary<string,  string>();
                debugInformation["Error"] = e.Message;
                debugInformation["ExecptionType"] = e.GetType().Name;
                debugInformation["FunctionName"] = "UsersGetAsync";
		        debugInformation["Route"] = "users";
		        debugInformation["Operation"] = "get";
		        debugInformation["Payload"] = GetPayloadForExceptionLogging(request);

		        _logger.LogCritical(JsonConvert.SerializeObject(debugInformation));
		        throw;
            }}
        }}