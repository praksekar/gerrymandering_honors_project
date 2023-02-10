from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum
from gerrychain import Partition, MarkovChain
if TYPE_CHECKING:
    from voting_models import VotingModel
from linetimer import CodeTimer
from ensemble_generation import gen_ensemble

# Election: type = callable[]
class Party(Enum):
    """Enum to represent each political party participating in an election."""

    DEMOCRAT = 1
    REPUBLICAN = 2


class Candidate:
    """Class representing an election candidate."""

    party: Party
    name: str

    def __init__(self, party: Party, name: str) -> None:
        self.party = party
        self.name = name
    
    def __repr__(self) -> str:
        return "party = %s and name = %s" % (self.party.name, self.name)


class RankedChoiceBallot:
    """
    Class that represents the physical ballot a voter casts during a ranked
    choice election.  Each ballot is comprised of a ranked list of candidates.

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


def multi_seat_ranked_choice_election(ballots: list[RankedChoiceBallot], candidates: set[Candidate], n_winners: int) -> set[Candidate]:
    """
    Runs a multi-seat ranked choice election as defined in SEC. 332 of H.R. 3863: 
    https://www.congress.gov/bill/117th-congress/house-bill/3863/text#H5B874295C83F485198CC739EE6BB3CA6

    Arguments:
        ballots: list of all ballots considered for election
        candidates: set of all candidates being considered for election
        n_winners: number of seats to fill for election
    Returns:
        set of winning election candidates
    """

    continuing_candidates: set[Candidate] = candidates.copy()
    winners: set[Candidate] = set()
    multi_seat_threshold: float = len(ballots)/(1+n_winners)

    while len(continuing_candidates) + len(winners) > n_winners:
        # first, perform vote tabulation for this round and find candidates that exceed threshold
        tally: dict[Candidate, float] = {c:0 for c in continuing_candidates} # initializing votes of all continuing candidates to 0
        for ballot in ballots: 
            if ballot.curr_choice() in continuing_candidates:
                tally[ballot.curr_choice()] += ballot.weight
        above_threshold_candidates: set[Candidate] = {c for c, v in tally.items() if v > multi_seat_threshold}

        # do surplus tabulation round if there are candidates above threshold
        if len(above_threshold_candidates) > 0: 
            winners = winners | above_threshold_candidates # all candidates above the threshold are immediately declared as winners and added to the winners set
            # perform the vote transfer process for each candidate with a vote count higher than the threshold
            for above_threshold_candidate in above_threshold_candidates: 
                candidate_votes: float = tally[above_threshold_candidate]
                surplus_fraction: float = (multi_seat_threshold-candidate_votes)/candidate_votes
                # iterate through ballots for which the current above_threshold_candidate is the current choice.
                # for each such ballot, multiply its weight by the surplus fraction and then set its current choice to the next continuing candidate on that ballot.
                for ballot in ballots: 
                    if ballot.curr_choice() == above_threshold_candidate and not ballot.was_transferred: # find above threshold ballots that have not already been transferred in this round
                        ballot.weight *= surplus_fraction
                        ballot.next_continuing_choice(continuing_candidates)
                        ballot.was_transferred = True # this ballot needs to be marked as transferred so we don't accidentally transfer it again in the next iteration
            for ballot in ballots: # reset each ballot as not transferred for the next round of counting
                ballot.was_transferred = False 

        # otherwise, if there are no candidates above threshold, this is a candidate elimination round
        else: 
            min_candidate: Candidate = min(tally, key=tally.get) 
            continuing_candidates.remove(min_candidate) # remove candidate with the minimum votes
            # transfer each ballot for which the candidate was the current choice to the next continuing candidate on that ballot
            for ballot in ballots: 
                if ballot.curr_choice == min_candidate:
                    ballot.next_continuing_choice(continuing_candidates)                    

    # if we reach here, it means that the number of winners + continuing candidates is <= the number of required seats. So, return all of the winners and continuing candidates.
    return winners | continuing_candidates 


def gen_candidates(n_winners) -> set[Candidate]: 
    candidates: set[Candidate] = set()
    candidate_counter: int = 1
    for val in Party:
        for _ in range(n_winners):
            candidates.add(Candidate(val, "Candidate %d" % candidate_counter))
            candidate_counter += 1
    return candidates


def gen_precinct_ballots(partition: Partition, precID: int, voting_model: VotingModel) -> list[RankedChoiceBallot]:
    pass


def gen_mmd_ballots(partition: Partition, districtID: int, voting_model: VotingModel) -> list[RankedChoiceBallot]:
    pass


def run_mmd_election(partition: Partition, districtID: int, mmd_config: dict[int, int]) -> set[Candidate]:
    district_votes: list[RankedChoiceBallot] = []
    with CodeTimer("running gen_candidates"):
        district_candidates: list[Candidate] = gen_candidates(mmd_config[districtID]) 
    for precID in partition.subgraphs[districtID].nodes:
        with CodeTimer("running party_line_voting"):
            precinct_votes = party_line_voting(partition.graph.nodes[precID], district_candidates) # FIX MESSY candidate generation with method above
        district_votes += precinct_votes
    with CodeTimer("running tabulation"):
        return multi_seat_ranked_choice_election(district_votes, district_candidates, mmd_config[districtID])


def run_statewide_elections(partition: Partition, mmd_config: dict[int, list[int]], voting_model: VotingModel, election_func: Election) -> list[Candidate]:
    winners = []
    for districtID in partition.parts.keys():
        with CodeTimer("running mmd election"):
            winners += run_mmd_election(partition, districtID, mmd_config)
    return winners


def run_many_statewide_elections(chain: MarkovChain, mmd_config: dict[int, int], n_elections: int) -> list[list[Candidate]]:
    elections_results: list[list[Candidate]] = []
    with CodeTimer("generating ensemble of size %d" % n_elections):
        ensemble: list[Partition] = gen_ensemble(chain, n_elections)
    for map in ensemble:
        with CodeTimer("running district elections"):
            election_results = run_statewide_elections(map, mmd_config) 
        elections_results.append(election_results)
    return elections_results


def run_smd_election(partition: Partition):
    pass