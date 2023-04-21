import random
import run_config
from ..custom_types import Party, Ballot, Candidate, Precinct, Voter, VotingComparator
from linetimer import CodeTimer, linetimer
import logging
logger = logging.getLogger(__name__)


def party_line_voting_with_candidate_preference(x: Candidate, y: Candidate, voter: Voter):
    return


def curried_voting_comparator():
    pass


def party_line_voting_comparator(x: Candidate, y: Candidate, voter: Voter):
    if x.party == voter.party and y.party != voter.party:
        return 1
    elif x.party != voter.party and y.party == voter.party:
        return -1
    elif x.party == y.party:
        return random.choice([-1, 1])
