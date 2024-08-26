namespace Starterkit.Models.Question
{
    public class QuestionResponse
    {
        public int file_id { get; set; }
        public string session_id { get; set; }
        public List<QuestionAnswerPair> question_answer_pairs { get; set; }
    }
}
