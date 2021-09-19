        /// <summary>
        /// auto-generated function invocation.
        ///</summary>
        [FunctionName("{NAME}")]
        public async Task<IActionResult> {NAME}(
            [HttpTrigger(AuthorizationLevel.Function, "{OPERATION}", Route = "{PATH}")]
            HttpRequest request{PARAM_NAMES})
        {{
            try {{
                {CONVERT}{VALUE}await _service.{FACTORY_CALL}{NAME}({PARAMS});
                return {RESULT};
            }} catch(CaffoaClientError err) {{
                return err.Result;
            }} catch (Exception e) {{
                LogException(e, request, "{NAME}", "{PATH}", "{OPERATION}"{ADDITIONAL_ERROR_INFOS});
		        throw;
            }}
        }}