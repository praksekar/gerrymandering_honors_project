import random
from election import Party, Ballot, Candidate
from typing import Callable
from linetimer import CodeTimer


VotingModel: type = Callable[[dict], list[Ballot]]


def party_line_voting(precinct: dict[str, int | str], candidates: list[Candidate]) -> list[Ballot]:
    precinct_votes: list[Ballot] = []
    dem_candidates = [c for c in candidates if c.party == Party.DEMOCRAT]
    rep_candidates = [c for c in candidates if c.party == Party.REPUBLICAN]
    for _ in range(int(precinct["PRES12D"])):
        random.shuffle(dem_candidates)
        random.shuffle(rep_candidates)
        precinct_votes.append(Ballot(dem_candidates + rep_candidates))
    for _ in range(int(precinct["PRES12R"])):
        random.shuffle(dem_candidates)
        random.shuffle(rep_candidates)
        precinct_votes.append(Ballot(rep_candidates + dem_candidates))
    return precinct_votes