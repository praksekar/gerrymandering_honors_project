import random
import run_config
from ..custom_types import Party, RankedChoiceBallot, Candidate, Precinct
from linetimer import CodeTimer, linetimer
import logging
logger = logging.getLogger(__name__)


# find someway to generally do this for more than 2 parties
def party_line_voting(precinct: Precinct, candidates: list[Candidate]) -> list[RankedChoiceBallot]:
    prec_ballots: list[RankedChoiceBallot] = []
    dem_candidates = [c for c in candidates if c.party == Party.DEMOCRAT]
    rep_candidates = [c for c in candidates if c.party == Party.REPUBLICAN]
    for _ in range(precinct[run_config.DEM_VOTE_TALLY_COL]): 
        random.shuffle(dem_candidates)
        random.shuffle(rep_candidates)
        prec_ballots.append(RankedChoiceBallot(dem_candidates + rep_candidates))
    for _ in range(precinct[run_config.REP_VOTE_TALLY_COL]): 
        random.shuffle(dem_candidates)
        random.shuffle(rep_candidates)
        prec_ballots.append(RankedChoiceBallot(rep_candidates + dem_candidates))
    return prec_ballots


def party_line_voting_with_candidate_preference(voter_party: Party, candidates: list[Candidate]):
    return