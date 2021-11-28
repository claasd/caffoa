using System;
using System.Net;
using System.Net.Http;
using System.Text;
using DemoV1.Model;
using Newtonsoft.Json;

namespace DemoV1.Errors
{
    public class BaseError : Exception
    {
        public Error Error;

        public BaseError(string status, string message) : base(message)
        {
            
            Error = new Error()
            {
                Message = message,
                Status = status
            };
        }
        public HttpResponseMessage Result => new HttpResponseMessage(HttpStatusCode.BadRequest)
        {
            Content = new StringContent(JsonConvert.SerializeObject(Error), Encoding.UTF8, "application/json")
        };
    }

    
}