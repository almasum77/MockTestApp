namespace Starterkit.Models.Test
{
	public class UserAnswerDetail
	{
		public int question_id { get; set; }
		public string user_answer { get; set; }
		public string correct_answer { get; set; }
		public bool? is_correct { get; set; }
	}
}
