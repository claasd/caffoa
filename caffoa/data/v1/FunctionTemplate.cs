using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using System.Net.Http;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

{IMPORTS}
namespace {NAMESPACE}
{{
    /// AUTO GENERATED CLASS
    /// implement a partial class that implements
    /// public static {INTERFACENAME} Service(HttpRequestMessage req, ILogger log);
    public static partial class {CLASSNAME}
    {{
{METHODS}
        private static async Task<string> GetPayloadForExceptionLogging(HttpRequestMessage req)
        {{
	        try
	        {{
		        var bytes = await req.Content.ReadAsByteArrayAsync();
		        if (bytes.Length > 0)
		        {{
			        return Convert.ToBase64String(bytes);
		        }}

		        return "no payload";
	        }}
	        catch (Exception e)
	        {{
		        return "error while reading payload: " + e.Message;
	        }}
        }}
    }}
}}