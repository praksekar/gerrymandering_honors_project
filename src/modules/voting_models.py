from __future__ import annotations
from typing import TYPE_CHECKING
import random
import run_config
from .election import Party, RankedChoiceBallot, Candidate


Precinct: type = dict[str, int|str]
# VotingModel: type = callable[[Precinct, list[Candidate]], list[RankedChoiceBallot]]


# find someway to generally do this for more than 2 parties
def party_line_voting(voter_party, candidates: list[Candidate]) -> RankedChoiceBallot:
    dem_candidates = [c for c in candidates if c.party == Party.DEMOCRAT]
    rep_candidates = [c for c in candidates if c.party == Party.REPUBLICAN]
    random.shuffle(dem_candidates)
    random.shuffle(rep_candidates)
    if voter_party == Party.DEMOCRAT:
        return RankedChoiceBallot(dem_candidates + rep_candidates)
    else:
        return RankedChoiceBallot(rep_candidates + dem_candidates)


def party_line_voting_with_candidate_preference(precinct: Precinct, candidates: list[Candidate]):
    return