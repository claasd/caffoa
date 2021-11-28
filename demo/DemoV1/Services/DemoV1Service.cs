using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using DemoV1.Errors;
using DemoV1.Model;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace DemoV1.Services
{
    public class DemoV1Service : IDemoV1Service
    {
        private readonly UserRepository<UserWithId> _users = new UserRepository<UserWithId>();
        private readonly UserRepository<GuestUser> _guests = new UserRepository<GuestUser>();
        
        public T ParseWithErrorHandling<T>(string requestBody)
        {
            if (string.IsNullOrWhiteSpace(requestBody))
                throw new BaseError("NoContent", "Payload is empty");
            try
            {
                return JsonConvert.DeserializeObject<T>(requestBody);
            }
            catch (Exception e)
            {
                while (e.InnerException != null)
                    e = e.InnerException;
                throw new BaseError(e.GetType().ToString(), e.Message);
            }
        }

        static HttpResponseMessage JsonResult(object data, HttpStatusCode code = HttpStatusCode.OK)
        {
            return new HttpResponseMessage(code)
            {
                Content = new StringContent(JsonConvert.SerializeObject(data), Encoding.UTF8, "application/json")
            };
        }
        public async Task<HttpResponseMessage> UsersGetAsync()
        {
            var result = new List<AnyCompleteUser>();
            result.AddRange(await _users.List());
            result.AddRange(await _guests.List());
            return JsonResult(result);
        }

        public async Task<HttpResponseMessage> UserPostAsync(HttpContent contentPayload)
        {
            var requestBody = await contentPayload.ReadAsStringAsync();
            try
            {
                var user = ParseWithErrorHandling<User>(requestBody);
                return await UserPutAsync(Guid.NewGuid().ToString(), user);
            }
            catch (BaseError e1)
            {
                try
                {
                    var guestUser = ParseWithErrorHandling<GuestUser>(requestBody);
                    return await UserPutAsync(guestUser.Email, guestUser);
                }
                catch (BaseError e2)
                {
                    throw new BaseError(
                        "WrongUserType",
                        $"Could not parse payload as regular user or guest user: {e1.Message} <> {e2.Message}");
                }
            }
        }

        public async Task<HttpResponseMessage> UserPutAsync(string userId, HttpContent contentPayload)
        {
            var requestBody = await contentPayload.ReadAsStringAsync();
            try
            {
                var payload = ParseWithErrorHandling<User>(requestBody);
                return await UserPutAsync(userId, payload);
            }
            catch (BaseError e1)
            {
                try
                {
                    var payload = ParseWithErrorHandling<GuestUser>(requestBody);
                    return await UserPutAsync(userId, payload);
                }
                catch (BaseError e2)
                {
                    throw new BaseError(
                        "WrongUserType",
                        $"Could not parse payload as regular user or guest user: {e1.Message} <> {e2.Message}");
                }
            }
        }
        
        private async Task<HttpResponseMessage> UserPutAsync(string userId, GuestUser guestUser)
        {
            if (guestUser.Email != userId)
            {
                throw new GuestUserNotValidError();
            }

            try
            {
                await _guests.GetById(userId);
                await _guests.Edit(guestUser.Email, guestUser);
                return JsonResult(guestUser);
            }
            catch (UserNotFoundError)
            {
                await _guests.Add(guestUser.Email, guestUser);
                return JsonResult(guestUser, HttpStatusCode.Created);
            }
        }

        private async Task<HttpResponseMessage> UserPutAsync(string userId, User payload)
        {
            try
            {
                var user = await _users.GetById(userId);
                user.UpdateWithUser(payload);
                await _users.Edit(user.Id, user);
                return JsonResult(user);
            }
            catch (UserNotFoundError)
            {
                var newUser = new UserWithId()
                {
                    Id = userId
                };
                newUser.UpdateWithUser(payload);
                await _users.Add(newUser.Id, newUser);
                return JsonResult(newUser, HttpStatusCode.Created);
            }
        }

        public async Task<HttpResponseMessage> UserPatchAsync(string userId, HttpContent contentPayload)
        {
            var requestBody = await contentPayload.ReadAsStringAsync();
            var patch = ParseWithErrorHandling<JObject>(requestBody);
            var user = await _users.GetById(userId);
            try
            {
                user.MergeWithUser(patch);
            }
            catch (Exception e)
            {
                while (e.InnerException != null)
                    e = e.InnerException;
                throw new BaseError(e.GetType().ToString(), e.Message);
            }

            await _users.Edit(user.Id, user);
            return JsonResult(user);
        }

        public async Task<HttpResponseMessage> UserGetAsync(string userId)
        {
            var user = await _users.GetById(userId);
            return JsonResult(user);
        }
    }
}