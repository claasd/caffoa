using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

{IMPORTS}
namespace {NAMESPACE}
{{
    /// AUTO GENERATED CLASS
    public class {CLASSNAME}
    {{
        private readonly ILogger<{CLASSNAME}> _logger;
        private readonly {INTERFACENAME} _service;
        public {CLASSNAME}(ILogger<{CLASSNAME}> logger, {INTERFACENAME} service) {{
            _logger = logger;
            _service = service;
        }}
{METHODS}
        private static string GetPayloadForExceptionLogging(HttpRequest req)
        {{
	        try
	        {{
		        if (req.ContentLength == 0)
                    return "no payload";

                using var ms = new MemoryStream();
                req.Body.CopyTo(ms);
                return Convert.ToBase64String(ms.ToArray());
	        }}
	        catch (Exception e)
	        {{
		        return "error while reading payload: " + e.Message;
	        }}
        }}
    }}
}}