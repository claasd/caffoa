using System;
using DemoV2.Model;
using Microsoft.AspNetCore.Mvc;

namespace DemoV2.Errors
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
        public IActionResult Result => new JsonResult(Error) {StatusCode = 400};
    }

    
}