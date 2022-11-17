import random
from ranked_choice_election import Party, Vote, Candidate
from typing import Callable, Dict

VotingModel = Callable[[dict], list[Vote]]


def party_line_voting(precinct: dict[str, int|str], candidates: list[Candidate]) -> list[Vote]:
    precinct_votes: list[Vote] = []
    dem_candidates = [c for c in candidates if c.party == Party.DEMOCRAT]
    rep_candidates = [c for c in candidates if c.party == Party.REPUBLICAN]
    for _ in range(int(precinct["PRES12D"])):
        random.shuffle(dem_candidates)
        precinct_votes += Vote(dem_candidates)
    for _ in range(int(precinct["PRES12R"])):
        random.shuffle(rep_candidates)
        precinct_votes += Vote(rep_candidates)
    return precinct_votes