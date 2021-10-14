using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

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
        public async Task<T> ParseJson<T>(Stream s)
        {{
            string requestBody = String.Empty;
            using (StreamReader streamReader =  new  StreamReader(s))
                requestBody = await streamReader.ReadToEndAsync();
            if (string.IsNullOrWhiteSpace(requestBody))
                throw {JSON_ERROR_CLASS}.NoContent();
            try {{
                return JsonConvert.DeserializeObject<T>(requestBody);
            }} catch (Exception e) {{
                throw {JSON_ERROR_CLASS}.FromException(e);
            }}
        }}

        public T ToObject<T>(JObject jObject)
        {{
            try {{
                return jObject.ToObject<T>();
            }} catch (Exception e) {{
                throw {JSON_ERROR_CLASS}.FromException(e);
            }}
        }}

        public void LogException(Exception e, HttpRequest request, string functionName, string route, string operation,
            params (string, object)[] namedParams)
        {{
            var debugInformation = new Dictionary<string,  string>();
            debugInformation["Error"] = e.Message;
            debugInformation["ExecptionType"] = e.GetType().Name;
            debugInformation["FunctionName"] = functionName;
            debugInformation["Route"] = route;
            debugInformation["Operation"] = operation;
            foreach (var (name,value) in namedParams)
            {{
                debugInformation["p_" + name] = value.ToString();
            }}
            debugInformation["Payload"] = GetPayloadForExceptionLogging(request);
            _logger.LogCritical(JsonConvert.SerializeObject(debugInformation));
        }}

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