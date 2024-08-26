using Starterkit.Models.Question;
using System.Linq;
using System.Text.Json;
using System.Text;
using System.Net.Http.Headers;
using Microsoft.JSInterop;
using Starterkit.Utilities;

namespace Starterkit.Services
{
    public class QuestionService
    {
        private readonly HttpClient _httpClient;

        public QuestionService(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }

        public async Task<QuestionResponse> GenerateQuestionsAsync(Stream fileStream, string fileName, int questionSize, List<string> questionTypes)
        {
            var content = new MultipartFormDataContent();
            content.Add(new StreamContent(fileStream), "file", fileName); 

            var queryParameters = new Dictionary<string, string>
            {
                { "question_size", questionSize.ToString() },
                { "question_types", string.Join("&question_types=", questionTypes) }  
            };

            var url = $"{ApiConfig.BaseUrl}/generate-questions/?" + string.Join("&", queryParameters.Select(kv => $"{kv.Key}={kv.Value}"));

            if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
            }

            var response = await _httpClient.PostAsync(url, content);

            if (response.IsSuccessStatusCode)
            {
                var responseData = await response.Content.ReadFromJsonAsync<QuestionResponse>();
                return responseData;
            }

            return null;
        }


        public async Task<bool> SaveQuestionsAndAnswersAsync(List<QuestionAnswerPair> questionAnswerPairs, int fileId)
        {
            var questionAnswerPairsToSend = questionAnswerPairs.Where(s=>s.answer!=null).Select(pair => new
            {
                question = pair.question,
                question_type = pair.question_type,
                answer = pair.answer
            }).ToList();

            var requestData = new
            {
                fileid = fileId,  
                question_answer_pairs = questionAnswerPairsToSend
            };

            var jsonPayload = JsonSerializer.Serialize(requestData);
            Console.WriteLine($"Payload: {jsonPayload}");

            if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
            }

            var response = await _httpClient.PostAsJsonAsync($"{ApiConfig.BaseUrl}/save-questions-and-answers/", requestData);

            if (!response.IsSuccessStatusCode)
            {
                Console.WriteLine($"Failed with status code: {response.StatusCode}");
                Console.WriteLine($"Reason: {response.ReasonPhrase}");
            }

            return response.IsSuccessStatusCode;
        }


		public async Task<List<FileQuestionSummary>> GetFileQuestionSummariesAsync()
		{
			var url = $"{ApiConfig.BaseUrl}/file-question-summaries/";

			if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
			{
				_httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
			}

			var response = await _httpClient.GetAsync(url);

			if (response.IsSuccessStatusCode)
			{
				var responseData = await response.Content.ReadFromJsonAsync<List<FileQuestionSummary>>();
				return responseData ?? new List<FileQuestionSummary>(); 
			}

			Console.WriteLine($"Failed to retrieve data. Status code: {response.StatusCode}");

			return new List<FileQuestionSummary>(); 
		}

        public async Task<FileQuestionSummary> GetFileQuestionSummaryAsync(int fileId)
        {
            var url = $"{ApiConfig.BaseUrl}/file-question-summaries/{fileId}";

            // Ensure the token is added to the Authorization header
            if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
            }

            var response = await _httpClient.GetAsync(url);

            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<FileQuestionSummary>();
            }

            return null; 
        }

        public async Task<List<QuestionAnswerPair>> GetQuestionsForFileAsync(int fileId)
        {
            var url = $"{ApiConfig.BaseUrl}/file-questions/{fileId}";

            // Ensure the token is added to the Authorization header
            if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
            }

            var response = await _httpClient.GetAsync(url);

            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<List<QuestionAnswerPair>>();
            }

            return new List<QuestionAnswerPair>(); 
        }


        public async Task<List<QuestionAnswerPairNew>> GetQuestionsForFileAsyncForTest(int fileId)
        {
            var url = $"{ApiConfig.BaseUrl}/file-questions-new/{fileId}";

            // Ensure the token is added to the Authorization header
            if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
            }

            var response = await _httpClient.GetAsync(url);

            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadFromJsonAsync<List<QuestionAnswerPairNew>>();
            }

            return new List<QuestionAnswerPairNew>();
        }

        public async Task<string> GetFileContentAsync(int fileId)
        {
            if (!string.IsNullOrEmpty(CommonConstants.AuthToken))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", CommonConstants.AuthToken);
            }

            var response = await _httpClient.GetAsync($"{ApiConfig.BaseUrl}/file-content/{fileId}");

            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadAsStringAsync();
            }

            return null;
        }



    }






}
