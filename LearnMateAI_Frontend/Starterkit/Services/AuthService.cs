using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Text.Json;
using System.Text;
using System.Net.Http.Headers;
using System.Text.Json.Serialization;
using Starterkit.Models.Auth;
using System.Net;
using Microsoft.JSInterop;
using Starterkit.Models;
using Starterkit.Utilities;

public class AuthService
{
    private readonly HttpClient _httpClient;
    private readonly IJSRuntime _jsRuntime;
    private readonly UserInfoContextService _userContext;

    public AuthService(HttpClient httpClient, IJSRuntime jsRuntime, UserInfoContextService userContext)
    {
        _httpClient = httpClient;
        _jsRuntime = jsRuntime;
        _userContext = userContext;
    }

    public async Task<bool> Login(string email, string password)
    {
        var loginData = new { email, password };
		var url = $"{ApiConfig.BaseUrl}/login";
		var response = await _httpClient.PostAsJsonAsync(url, loginData);

        if (response.IsSuccessStatusCode)
        {
            var responseContent = await response.Content.ReadAsStringAsync();
            var tokenResponse = JsonSerializer.Deserialize<TokenResponse>(responseContent);

            if (!string.IsNullOrEmpty(tokenResponse.AccessToken))
            {
                await _jsRuntime.InvokeVoidAsync("localStorage.setItem", "authToken", tokenResponse.AccessToken);
                CommonConstants.AuthToken = tokenResponse.AccessToken;
                await LoadCurrentUser();
                return true;
            }
        }
        return false;
    }

    public async Task<bool> SignUp(User newUser)
    {
        try
        {
            var url = $"{ApiConfig.BaseUrl}/signup";
            var response = await _httpClient.PostAsJsonAsync(url, newUser);

            // Check if the request was successful
            if (response.IsSuccessStatusCode)
            {
                return true; // Signup was successful
            }
            else if (response.StatusCode == HttpStatusCode.BadRequest)
            {
                // Check if the email is already registered
                var errorResponse = await response.Content.ReadAsStringAsync();
                if (errorResponse.Contains("Email already registered"))
                {
                    throw new HttpRequestException("This email is already registered.", null, response.StatusCode);
                }
                else
                {
                    throw new HttpRequestException("Signup failed. Please check your details.", null, response.StatusCode);
                }
            }
            else
            {
                throw new HttpRequestException("An error occurred during signup.", null, response.StatusCode);
            }
        }
        catch (Exception ex)
        {
            // Handle exceptions (e.g., network issues)
            throw new HttpRequestException($"An error occurred: {ex.Message}");
        }
    }

    public async Task LoadCurrentUser()
    {
        var token = await _jsRuntime.InvokeAsync<string>("localStorage.getItem", "authToken");

        if (!string.IsNullOrEmpty(token))
        {
            _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
			var url = $"{ApiConfig.BaseUrl}/users/me/";
			var response = await _httpClient.GetAsync(url);
            if (response.IsSuccessStatusCode)
            {
                var responseContent = await response.Content.ReadAsStringAsync();
                User user = JsonSerializer.Deserialize<User>(responseContent, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });
                await _userContext.InitializeUserContext(user);
            }
        }
    }

    public async Task Logout()
    {
        await _userContext.ClearUserContext();
    }

    public async Task<User> GetCurrentUser()
    {
        var token = await _jsRuntime.InvokeAsync<string>("localStorage.getItem", "authToken");

        if (string.IsNullOrEmpty(token))
        {
            return null;
        }

        _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

        var response = await _httpClient.GetAsync("/users/me/");

        if (response.IsSuccessStatusCode)
        {
            var responseContent = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<User>(responseContent, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });
        }
        else
        {
            // Handle error (e.g., unauthorized, etc.)
            return null;
        }
    }
}


public class TokenResponse
{
    [JsonPropertyName("access_token")]
    public string AccessToken { get; set; }

    [JsonPropertyName("token_type")]
    public string TokenType { get; set; }
}

