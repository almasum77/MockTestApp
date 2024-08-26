using Starterkit.Models.Test;
using Starterkit.Utilities;
using System.Net.Http;
using System.Net.Http.Headers;

namespace Starterkit.Services
{
    public class TestService
    {
        private readonly HttpClient _httpClient;

        public TestService(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }
        public async Task<bool> SaveTestAndAnswersAsync(int fileId, TestResult result, List<UserAnswerSubmission> userAnswers)
        {
            var requestData = new
            {
                fileid = fileId,
                score = result.Score,
                total_questions = result.TotalQuestions,
                correct_answers = result.CorrectAnswers,
                user_answers = userAnswers // Include the user's answers
            };

            if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
            }

            var response = await _httpClient.PostAsJsonAsync($"{ApiConfig.BaseUrl}/submit-answers/", requestData);

            return response.IsSuccessStatusCode;
        }



    }
}
