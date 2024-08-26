using Microsoft.JSInterop;
using Starterkit.Models.Auth;
using System.Net.Http;
using System.Text.Json;

namespace Starterkit.Models
{
    public class UserInfoContextService
    {
        private readonly IJSRuntime _jsRuntime;
        private readonly HttpClient _httpClient;

        public UserInfo userInfo { get;  set; }

        public UserInfoContextService(IJSRuntime jsRuntime, HttpClient httpClient)
        {
            _jsRuntime = jsRuntime;
            _httpClient = httpClient;
            
        }

        public async Task InitializeUserContext(User user)
        {
            userInfo = new UserInfo();
            if (user != null)
            {
                userInfo.firstname = user.firstname;
                userInfo.lastname = user.lastname;
                userInfo.email = user.email;
            }
        }

        public async Task ClearUserContext()
        {
            userInfo = null;
            await _jsRuntime.InvokeVoidAsync("localStorage.removeItem", "authToken");
        }
    }
}
