using System.ComponentModel.DataAnnotations;

namespace Starterkit.Models.Auth
{
    public class User
    {
        public int userid { get; set; }

        [Required(ErrorMessage = "First Name is required.")]
        public string firstname { get; set; }

        [Required(ErrorMessage = "Last Name is required.")]
        public string lastname { get; set; }

        //[Required(ErrorMessage = "Email is required.")]
        //[EmailAddress(ErrorMessage = "Invalid email format.")]
        public string email { get; set; }

        public string password { get; set; }
    }

}
