namespace Starterkit.Models.Question
{
    public class Question
    {
        //    questionid = Column(Integer, primary_key= True, index= True)
        //fileid = Column(Integer, ForeignKey('files.fileid'))  # Foreign key in lowercase
        //questiontext = Column(Text, nullable= False)
        //questiontype = Column(String(20), nullable=False)  # 'FillInTheBlanks' or 'TrueFalse'
        //createddate = Column(DateTime(timezone= True), server_default=func.now())
        //createdby = Column(Integer, nullable= True)

        public int questionid { get; set; }
        public int fileid { get; set; }
        public string questiontext { get; set; }
        public string questiontype { get; set; }
        public DateTime createddate { get; set; }
        public int createdby { get; set; }

    }
}
