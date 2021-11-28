using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using DemoV2.Errors;
using DemoV2.Model;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace DemoV2.Services
{
    public class DemoV3Service : IDemoV2Service
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

        public async Task<IActionResult> UsersGetAsync(HttpRequest request)
        {
            var result = new List<AnyCompleteUser>();
            result.AddRange(await _users.List());
            result.AddRange(await _guests.List());
            return new JsonResult(result);
        }

        public async Task<IActionResult> UserPostAsync(HttpRequest request)
        {
            string requestBody;
            using (var streamReader = new StreamReader(request.Body))
                requestBody = await streamReader.ReadToEndAsync();
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

        public async Task<IActionResult> UserPutAsync(string userId, HttpRequest request)
        {
            string requestBody;
            using (var streamReader = new StreamReader(request.Body))
                requestBody = await streamReader.ReadToEndAsync();
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

        private async Task<IActionResult> UserPutAsync(string userId, GuestUser guestUser)
        {
            if (guestUser.Email != userId)
            {
                throw new GuestUserNotValidError();
            }

            try
            {
                await _guests.GetById(userId);
                await _guests.Edit(guestUser.Email, guestUser);
                return new JsonResult(guestUser);
            }
            catch (UserNotFoundError)
            {
                await _guests.Add(guestUser.Email, guestUser);
                return new JsonResult(guestUser) { StatusCode = 201 };
            }
        }

        private async Task<IActionResult> UserPutAsync(string userId, User payload)
        {
            try
            {
                var user = await _users.GetById(userId);
                user.UpdateWithUser(payload);
                await _users.Edit(user.Id, user);
                return new JsonResult(user);
            }
            catch (UserNotFoundError)
            {
                var newUser = new UserWithId()
                {
                    Id = userId
                };
                newUser.UpdateWithUser(payload);
                await _users.Add(newUser.Id, newUser);
                return new JsonResult(newUser) { StatusCode = 201 };
            }
        }

        public async Task<IActionResult> UserPatchAsync(string userId, HttpRequest request)
        {
            string requestBody;
            using (var streamReader = new StreamReader(request.Body))
                requestBody = await streamReader.ReadToEndAsync();
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
            return new JsonResult(user);
        }

        public async Task<IActionResult> UserGetAsync(string userId, HttpRequest request)
        {
            var user = await _users.GetById(userId);
            return new JsonResult(user);
        }
    }
}