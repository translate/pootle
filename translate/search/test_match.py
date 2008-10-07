from translate.search import match
from translate.storage import csvl10n

class TestMatch:
    """Test the matching class"""
    def candidatestrings(self, units):
        """returns only the candidate strings out of the list with (score, string) tuples"""
        return [unit.source for unit in units]

    def buildcsv(self, sources, targets=None):
        """Build a csvfile store with the given source and target strings"""
        if targets is None:
            targets = sources
        else:
            assert len(sources) == len(targets)
        csvfile = csvl10n.csvfile()
        for source, target in zip(sources, targets):
            unit = csvfile.addsourceunit(source)
            unit.target = target
        return csvfile
            
    def test_matching(self):
        """Test basic matching"""
        csvfile = self.buildcsv(["hand", "asdf", "fdas", "haas", "pond"])
        matcher = match.matcher(csvfile)
        candidates = self.candidatestrings(matcher.matches("hond"))
        candidates.sort()
        assert candidates == ["hand", "pond"]
        message = "Ek skop die bal"
        csvfile = self.buildcsv(
            ["Hy skop die bal", 
            message, 
            "Jannie skop die bal", 
            "Ek skop die balle", 
            "Niemand skop die bal nie"])
        matcher = match.matcher(csvfile)
        candidates = self.candidatestrings(matcher.matches(message))
        assert len(candidates) == 3
        #test that the 100% match is indeed first:
        assert candidates[0] == message
        candidates.sort()
        assert candidates[1:] == ["Ek skop die balle", "Hy skop die bal"]

    def test_multiple_store(self):
        """Test using multiple datastores"""
        csvfile1 = self.buildcsv(["hand", "asdf", "fdas"])
        csvfile2 = self.buildcsv(["haas", "pond"])
        matcher = match.matcher([csvfile1, csvfile2])
        candidates = self.candidatestrings(matcher.matches("hond"))
        candidates.sort()
        assert candidates == ["hand", "pond"]
        message = "Ek skop die bal"
        csvfile1 = self.buildcsv(
            ["Hy skop die bal", 
            message, 
            "Jannie skop die bal"])
        csvfile2 = self.buildcsv(
            ["Ek skop die balle", 
            "Niemand skop die bal nie"])
        matcher = match.matcher([csvfile1, csvfile2])
        candidates = self.candidatestrings(matcher.matches(message))
        assert len(candidates) == 3
        #test that the 100% match is indeed first:
        assert candidates[0] == message
        candidates.sort()
        assert candidates[1:] == ["Ek skop die balle", "Hy skop die bal"]

    def test_extendtm(self):
        """Test that we can extend the TM after creation."""
        message = "Open file..."
        csvfile1 = self.buildcsv(["Close application", "Do something"])
        matcher = match.matcher([csvfile1])
        candidates = self.candidatestrings(matcher.matches(message))
        assert len(candidates) == 0
        csvfile2 = self.buildcsv(["Open file"])
        matcher.extendtm(csvfile2.units, store=csvfile2)
        candidates = self.candidatestrings(matcher.matches(message))
        assert len(candidates) == 1
        assert candidates[0] == "Open file"

    def test_terminology(self):
        csvfile = self.buildcsv(["file", "computer", "directory"])
        matcher = match.terminologymatcher(csvfile)
        candidates = self.candidatestrings(matcher.matches("Copy the files from your computer"))
        candidates.sort()
        assert candidates == ["computer", "file"]

