namespace Starterkit.Models.Test
{
	public class TestDetail
	{
		public int testid { get; set; }
		public string testno { get; set; }
		public int userid { get; set; }
		public int fileid { get; set; }
		public string filename { get; set; }
		public DateTime testdate { get; set; }
		public int? score { get; set; } = 0;
		public int? totalquestions { get; set; } = 0;
        public int? correctanswers { get; set; } = 0;
        public List<TestQuesitonAnswerDetails> user_answers { get; set; }
	}
}
