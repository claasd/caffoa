using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using DemoV3.Errors;
using DemoV3.Model;
using Microsoft.AspNetCore.Http;
using Newtonsoft.Json.Linq;

namespace DemoV3.Services
{
    
    public class DemoV3Service : IDemoV3Service, IDemoV3ServiceFactory
    {
        private readonly UserRepository<UserWithId> _users = new UserRepository<UserWithId>();
        private readonly UserRepository<GuestUser> _guests = new UserRepository<GuestUser>();
        public IDemoV3Service Instance(HttpRequest request)
        {
            return this;
        }
        
        public async Task<IEnumerable<AnyCompleteUser>> UsersGetAsync()
        {
            var result = new List<AnyCompleteUser>();
            result.AddRange(await _users.List());
            result.AddRange(await _guests.List());
            return result;
        }

        public async Task<AnyCompleteUser> UserPostAsync(User payload)
        {
            var (user, _) = await UserPutAsync(Guid.NewGuid().ToString(), payload);
            return user;
        }

        public async Task<AnyCompleteUser> UserPostAsync(GuestUser payload)
        {
            var (user,_) = await UserPutAsync(payload.Email, payload);
            return user;
        }

        public async Task<(AnyCompleteUser, int)> UserPutAsync(string userId, User payload)
        {
            try
            {
                var user = await _users.GetById(userId);
                user.UpdateWithUser(payload);
                await _users.Edit(user.Id, user);
                return (user, 200);
            }
            catch (UserNotFoundError)
            {
                var newUser = new UserWithId()
                {
                    Id = userId
                };
                newUser.UpdateWithUser(payload);
                await _users.Add(newUser.Id, newUser);
                return (newUser, 201);
            }
        }

        public async Task<(AnyCompleteUser, int)> UserPutAsync(string userId, GuestUser payload)
        {
            if (payload.Email != userId)
            {
                throw new GuestUserNotValidError();
            }
            try
            {
                await _guests.GetById(userId);
                await _guests.Edit(payload.Email, payload);
                return (payload, 200);
            }
            catch (UserNotFoundError)
            {
                await _guests.Add(payload.Email, payload);
                return (payload, 201);
            }

            
            
            
        }

        public async Task<UserWithId> UserPatchAsync(string userId, JObject payload)
        {
            var user = await _users.GetById(userId);
            user.MergeWithUser(payload);
            await _users.Edit(user.Id, user);
            return user;
        }

        public async Task<UserWithId> UserGetAsync(string userId)
        {
            return await _users.GetById(userId);
        }
    }
}