import sys
from enum import Enum


class Party(Enum):
    DEMOCRAT = 1
    REPUBLICAN = 2


class Candidate:
    def __init__(self, party: Party, name: str) -> None:
        self.party = party
        self.name = name
    
    def __repr__(self):
        return "party = %s and name = %s" % (self.party.name, self.name)
    

class Vote:
    weight: float = 1
    def __init__(self, ranked_choices: list[Candidate]) -> None:
        self.curr_choice = iter(ranked_choices)
    
    def get_next_choice(self) -> Candidate:
        return next(self.curr_choice)


Tally = dict[Candidate, list[list[Vote], float]]


def ranked_choice_tabulation(district_votes: list[Vote], district_candidates: list[Candidate], n_req_winners: int) -> set[Candidate]:
    winners: set[Candidate] = set()
    threshold: float = len(district_votes)/(1+n_req_winners)
    continuing_tally: Tally = {}
    for c in district_candidates:
        continuing_tally[c] = [[], 0]
    for v in district_votes:
        next = v.get_next_choice()
        continuing_tally[next][0].append(v)
        continuing_tally[next][1] += v.weight
    
    while len(continuing_tally) + len(winners) > n_req_winners:
        above_threshold_candidates: list[Candidate] = [k for k, v in continuing_tally.items() if v[1] > threshold]
        if len(above_threshold_candidates) > 0: # surplus tabulation round
            for c in above_threshold_candidates:
                candidate_votes: list[Vote] = continuing_tally[c][0]
                weighted_vote_count: float = continuing_tally[c][1]
                surplus_fraction: float = (threshold-weighted_vote_count)/weighted_vote_count
                for v in candidate_votes:
                    next: Candidate = v.get_next_choice()
                    v.weight *= surplus_fraction
                    if next in continuing_tally:
                        continuing_tally[next][0].append(v) # because we remove eliminated and above threshold candidates, check to see if next choice is still in the continuing tally dict
                        continuing_tally[next][1] += v.weight
            for c in above_threshold_candidates:
                continuing_tally.pop(c)
            winners = winners | set(above_threshold_candidates)
        else: # candidate elimination round
            min_candidate: Candidate = None
            min_votes: int = sys.maxsize
            for c, val in continuing_tally.items():
                if val[1] < min_votes:
                    min_candidate = c
                    min_votes = val[1]
            for v in continuing_tally[min_candidate][0]:
                next: Candidate = v.get_next_choice()
                if next in continuing_tally:
                    continuing_tally[next].append(v)
                    continuing_tally[next][1] += v.weight
            continuing_tally.pop(min_candidate)
    winners = winners | continuing_tally.keys()
    assert len(winners) <= n_req_winners
    return list(winners)


def gen_candidates(n_winners) -> list[Candidate]: 
    candidates: list[Candidate] = []
    candidate_counter: int = 1
    for val in Party:
        for _ in range(n_winners):
            candidates.append(Candidate(val, "Candidate %d" % candidate_counter))
            candidate_counter += 1
    return candidates