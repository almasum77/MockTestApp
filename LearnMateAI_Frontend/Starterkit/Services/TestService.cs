using Starterkit.Models.Test;
using Starterkit.Utilities;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using static Starterkit.Utilities.CommonConstants;

namespace Starterkit.Services
{
    public class TestService
    {
        private readonly HttpClient _httpClient;

        public TestService(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }
        public async Task<bool> SaveTestAndAnswersAsync(int fileId, TestResult result, string questionType, List<UserAnswerSubmission> userAnswers)
        {
            var requestData = new
            {
                fileid = fileId,
                score = result.Score,
                total_questions = result.TotalQuestions,
                correct_answers = result.CorrectAnswers,
                question_type = questionType,
                user_answers = userAnswers // Include the user's answers
            };

            // Serialize to JSON string and log it (for debugging purposes)
            var json = JsonSerializer.Serialize(requestData);
            Console.WriteLine(json);

            if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
            }

            var response = await _httpClient.PostAsJsonAsync($"{ApiConfig.BaseUrl}/submit-answers/", requestData);

            return response.IsSuccessStatusCode;
        }

		public async Task<List<TestSummary>> GetTestSummariesAsync()
		{
			var url = $"{ApiConfig.BaseUrl}/test-summaries";

			if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
			{
				_httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
			}

			var response = await _httpClient.GetAsync(url);

			if (response.IsSuccessStatusCode)
			{
				return await response.Content.ReadFromJsonAsync<List<TestSummary>>();
			}

			return null;
		}


		public async Task<TestDetail> GetTestDetailsAsync(int testId)
		{
			var url = $"{ApiConfig.BaseUrl}/test-details/{testId}";

			if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
			{
				_httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
			}

			var response = await _httpClient.GetAsync(url);

			if (response.IsSuccessStatusCode)
			{
				return await response.Content.ReadFromJsonAsync<TestDetail>();
			}

			return null;
		}

	}
}
