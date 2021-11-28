namespace DemoV2.Errors
{
    public class UserNotFoundError : BaseError
    {
        public UserNotFoundError() : base("UserNotFound", "The specified user was not found")
        {
        }
    }
}