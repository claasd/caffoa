using System.Net.Http;
using DemoV1.Services;
using Microsoft.Extensions.Logging;

namespace DemoV1
{
    
    public partial class DemoV1Functions
    {
        public static DemoV1Service DemoV1 = new DemoV1Service();
        public static IDemoV1Service Service(HttpRequestMessage req, ILogger log)
        {
            return DemoV1;
        }
    }
}