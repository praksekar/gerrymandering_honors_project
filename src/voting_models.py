from __future__ import annotations
import random
from election import Party, RankedChoiceBallot, Candidate


VotingModel: type = callable[[dict[str, int | str], list[Candidate]], list[RankedChoiceBallot]]


def party_line_voting(precinct: dict[str, int | str], candidates: list[Candidate]) -> list[RankedChoiceBallot]:
    precinct_votes: list[RankedChoiceBallot] = []
    dem_candidates = [c for c in candidates if c.party == Party.DEMOCRAT]
    rep_candidates = [c for c in candidates if c.party == Party.REPUBLICAN]
    for _ in range(int(precinct["PRES12D"])):
        random.shuffle(dem_candidates)
        random.shuffle(rep_candidates)
        precinct_votes.append(RankedChoiceBallot(dem_candidates + rep_candidates))
    for _ in range(int(precinct["PRES12R"])):
        random.shuffle(dem_candidates)
        random.shuffle(rep_candidates)
        precinct_votes.append(RankedChoiceBallot(rep_candidates + dem_candidates))
    return precinct_votes