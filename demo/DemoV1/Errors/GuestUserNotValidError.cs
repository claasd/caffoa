namespace DemoV1.Errors
{
    public class GuestUserNotValidError : BaseError 
    {
        public GuestUserNotValidError() : base("GuestUserNotValid", "The guest user's email must match the user-id")
        {
        }
    }
}