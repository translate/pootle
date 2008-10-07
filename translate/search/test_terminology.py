from translate.search import terminology

class TestTerminology:
    """Test terminology matching"""
    def test_basic(self):
        """Tests basic functionality"""
        termmatcher = terminology.TerminologyComparer()
        assert termmatcher.similarity("Open the file", "file") > 75
    
    def test_brackets(self):
        """Tests that brackets at the end of a term are ignored"""
        termmatcher = terminology.TerminologyComparer()
        assert termmatcher.similarity("Open file", "file (noun)") > 75
        assert termmatcher.similarity("Contact your ISP", "ISP (Internet Service Provider)") > 75

    def test_past_tences(self):
        """Tests matching of some past tenses"""
        termmatcher = terminology.TerminologyComparer()
        assert termmatcher.similarity("The bug was submitted", "submit") > 75
        assert termmatcher.similarity("The site is certified", "certify") > 75
        
    def test_space_mismatch(self):
        """Tests that we can match with some spacing mismatch"""
        termmatcher = terminology.TerminologyComparer()
        assert termmatcher.similarity("%d minutes downtime", "down time") > 75

    def test_hyphen_mismatch(self):
        """Tests that we can match with some spacing mismatch"""
        termmatcher = terminology.TerminologyComparer()
        assert termmatcher.similarity("You can preorder", "pre-order") > 75
        assert termmatcher.similarity("You can pre-order", "pre order") > 75
        assert termmatcher.similarity("You can preorder", "pre order") > 75
        assert termmatcher.similarity("You can pre order", "pre-order") > 75

