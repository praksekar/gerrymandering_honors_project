from enum import Enum


class Party(Enum):
    DEMOCRAT = 1
    REPUBLICAN = 2


class Candidate:
    def __init__(self, party: Party, name: str) -> None:
        self.party = party
        self.name = name
    
    def __repr__(self) -> str:
        return "party = %s and name = %s" % (self.party.name, self.name)


class Ballot:
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


def multi_seat_ranked_choice_election(ballots: list[Ballot], continuing_candidates: set[Candidate], n_winners: int) -> set[Candidate]:
    winners: set[Candidate] = set()
    multi_seat_threshold: float = len(ballots)/(1+n_winners)
    while len(continuing_candidates) + len(winners) > n_winners:
        tally: dict[Candidate, float] = {c:0 for c in continuing_candidates} #initialize to zeros!!!!
        for ballot in ballots: # doing counting for this round, filling in a tally
            if ballot.curr_choice() in continuing_candidates:
                tally[ballot.curr_choice()] += ballot.weight
        above_threshold_candidates: set[Candidate] = {c for c, v in tally.items() if v > multi_seat_threshold}

        if len(above_threshold_candidates) > 0: # surplus tabulation round
            winners = winners | above_threshold_candidates # all candidates above the threshold are immediately assigned as winners
            for above_threshold_candidate in above_threshold_candidates:
                candidate_votes: float = tally[above_threshold_candidate]
                surplus_fraction: float = (multi_seat_threshold-candidate_votes)/candidate_votes
                for ballot in ballots:
                    if ballot.curr_choice() == above_threshold_candidate and not ballot.was_transferred: # find above threshold ballots that have not already been transferred in this round
                        ballot.weight *= surplus_fraction
                        ballot.next_continuing_choice(continuing_candidates)
                        ballot.was_transferred = True # this ballot needs to be marked as transferred so we cannot transfer it again in the next iteration
            for ballot in ballots: # reset each ballot as not transferred for the next round of counting
                ballot.was_transferred = False 

        else: # candidate elimination round
            min_candidate: Candidate =  min(tally, key=tally.get) # get candidate from tally with the min votes
            continuing_candidates.remove(min_candidate)
            for ballot in ballots:
                if ballot.curr_choice == min_candidate:
                    ballot.next_continuing_choice(continuing_candidates)                    
    return winners | continuing_candidates # if we reach here, it means that the number of winners + continuing candidates is <= the number of required seats. So, return the union of both.


def gen_candidates(n_winners) -> set[Candidate]: 
    candidates: set[Candidate] = set()
    candidate_counter: int = 1
    for val in Party:
        for _ in range(n_winners):
            candidates.add(Candidate(val, "Candidate %d" % candidate_counter))
            candidate_counter += 1
    return candidates