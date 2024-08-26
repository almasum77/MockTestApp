namespace Starterkit.Models.Test
{
    public class SubmitAnswersRequest
    {
        public int fileid { get; set; }
        public int score { get; set; }
        public int total_questions { get; set; }
        public int correct_answers { get; set; }

        public List<UserAnswerSubmission> user_answers { get; set; }
    }
}
