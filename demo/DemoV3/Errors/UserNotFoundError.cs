using Demov3.Errors;
using DemoV3.Model;

namespace DemoV3.Errors
{
    public class UserNotFoundError : ErrorClientError
    {
        public UserNotFoundError()
        {
            Element = new Error()
            {
                Status = "UserNotFound",
                Message = "The specified user was not found"
            };
        }
    }
}