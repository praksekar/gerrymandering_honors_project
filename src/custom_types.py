from enum import Enum
from gerrychain import Partition
from typing import Callable, Dict, List


RepsPerDistrict: type = Dict[int, int]


class VMDPartition(Partition):
    """Class that extends Gerrychain Partition, adding a dict field mapping
    districts to the number of representatives in that district"""

    district_reps: RepsPerDistrict

    def __init__(self, *args, district_reps: RepsPerDistrict, **kwargs):
        self.district_reps = district_reps
        super(VMDPartition, self).__init__(*args, **kwargs)
    
    def __repr__(self):
        number_of_parts = len(self)
        s = "s" if number_of_parts > 1 else ""
        return "<%s [%d part%s], district reps: %s>" % (self.__class__.__name__, number_of_parts, s, str(self.district_reps))


class Party(Enum):
    """Enum to represent each political party participating in an election."""

    DEMOCRAT = 1
    REPUBLICAN = 2


class Candidate:
    """Class representing an election candidate."""

    party: Party
    name: str
    district: int
    favoritism: int

    def __init__(self, party: Party, name: str, district: int, favoritism: int) -> None:
        self.party = party
        self.name = name
        self.district = district
        self.favoritism = favoritism
    
    def __repr__(self) -> str:
        return "party = %s, name = %s, district = %s" % (self.party.name, self.name, self.district)


class RankedChoiceBallot:
    """
    Class that represents the physical ballot a voter casts during a ranked
    choice election. Each ballot is comprised of a ranked list of candidates.

    Fields:
        choices_left: remaining list of ranked candidates on ballot that have
        not yet been counted in a round of tabulation; the first element will be
        the candidate that this ballot will next count for
        was_transferred: flag to prevent double transfer of the same ballot
        during a surplus tabulation round in which there are multiple winners
        weight: used for summing the vote count for a candidate when this
        ballot is tabulated; is reweighted every surplus tabulation round
    
    Methods:
        curr_choice: returns candidate that this ballot will next count for (0th
        element of choices_left)
        next_continuing_choice: pops candidates from front of choices_left until
        a continuing candidate is at the front; used after each round to
        'transfer' a vote to the next candidate on that ballot
    """

    choices_left: list[Candidate]
    was_transferred: bool = False
    weight: float = 1

    def __init__(self, ranked_choices: list[Candidate]) -> None:
        self.choices_left = ranked_choices

    def curr_choice(self) -> Candidate:
        return self.choices_left[0]

    def next_continuing_choice(self, continuing_candidates: set[Candidate]) -> None:
        while self.choices_left[0] not in continuing_candidates:
            self.choices_left.pop(0)
        self.choices_left.pop(0)
    
    def __repr__(self) -> str:
        return "%s, weight = %f" % (str(self.choices_left), self.weight)


Precinct: type = Dict[str, int|str]
VotingModel: type = Callable[[Precinct, List[Candidate]], List[RankedChoiceBallot]]