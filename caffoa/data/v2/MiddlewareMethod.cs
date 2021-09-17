        /// <summary>
        /// {DOC}
        /// </summary>
        public async Task<IActionResult> {NAME}({PARAMS}) {{
            try {{
                var element = await _service.{NAME}({CALL_PARAMS});
                return new JsonResult({ELEMENT}) {{StatusCode = {CODE}}};
            }} catch(CaffoaClientError err) {{
                return err.Result;
            }}
        }}
