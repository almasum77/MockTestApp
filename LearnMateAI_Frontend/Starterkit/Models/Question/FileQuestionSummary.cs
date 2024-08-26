namespace Starterkit.Models.Question
{
	public class FileQuestionSummary
	{
		public int file_id { get; set; }
		public string original_filename { get; set; }
		public int number_of_questions { get; set; }
		public DateTime uploaddate { get; set; }
	}
}
