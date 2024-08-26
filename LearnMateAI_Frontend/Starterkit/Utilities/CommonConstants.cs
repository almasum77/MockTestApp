namespace Starterkit.Utilities
{
    public static class CommonConstants
    {
        public const string ApplicationName = "Learn Mate AI";
        public const int DefaultPageSize = 15;
        public const int DefaultQuestionSize = 5;
        public static string AuthToken { get; set; }

        public enum UserRoles
        {
            Admin,
            User,
            Guest
        }

        public enum QuestionType
        { 
        TrueFalse,
        FillInTheBlanks
        }
    }
}
