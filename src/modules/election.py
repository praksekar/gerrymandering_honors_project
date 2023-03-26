from gerrychain import Partition
from linetimer import CodeTimer, linetimer
from ..custom_types import VotingModel
import run_config
import logging
from pprint import pprint
logger = logging.getLogger(__name__)
from ..custom_types import RankedChoiceBallot, Candidate, Party 


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
                    if ballot.curr_choice() == above_threshold_candidate and not ballot.was_transferred: # select above threshold ballots that have not already been transferred in this round
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


def gen_mmd_candidates(n_seats: int, districtID: int) -> set[Candidate]: 
    """
    Generates a list of arbitrary candidates from each party. The number of
    candidates from each party is equal to the number of seats in the election
    as required by the general case in SEC. 203 of H.R. 3863.

    Arguments:
        n_seats: number of seats to be filled
    Returns:
        set of candidates being considered in an MMD
    """

    candidates: set[Candidate] = set()
    candidate_counter: int = 1
    for party in Party:
        for _ in range(n_seats):
            candidates.add(Candidate(party, "Candidate %d" % candidate_counter, districtID, 1))
            candidate_counter += 1
    return candidates


@linetimer(logger_func=logger.info)
def gen_mmd_ballots(partition: Partition, districtID: int, voting_model: VotingModel, candidates: list[Candidate]) -> list[RankedChoiceBallot]:
    mmd_ballots: list[RankedChoiceBallot] = []
    for precID in partition.subgraphs[districtID].nodes:
        mmd_ballots += voting_model(partition.graph.nodes[precID], candidates)
    return mmd_ballots


def run_district_election(partition: Partition, districtID: int, n_reps: int, voting_model: VotingModel) -> set[Candidate]:
    candidates: list[Candidate] = gen_mmd_candidates(n_reps, districtID)
    district_ballots: list[RankedChoiceBallot] = gen_mmd_ballots(partition, districtID, voting_model, candidates)
    return multi_seat_ranked_choice_election(district_ballots, candidates, n_reps)


def run_statewide_district_elections(partition: Partition, mmd_config: dict[int, int], voting_model: VotingModel) -> dict[int, set[Candidate]]:
    winners = dict.fromkeys(mmd_config.keys(), [])
    for districtID in partition.parts.keys():
        with CodeTimer("running mmd election for district %d" % districtID, logger_func=logger.info):
            winners[districtID] = run_district_election(partition, districtID, mmd_config[districtID], voting_model)
    return winners


def run_many_statewide_elections(ensemble: list[Partition], mmd_config: dict[int, int]) -> list[list[Candidate]]: 
    elections_results: list[list[Candidate]] = []
    for map in ensemble: 
        with CodeTimer("running district elections", logger_func=logger.info):
            election_results = run_statewide_district_elections(map, mmd_config) 
        elections_results.append(election_results)
    return elections_results


def run_smd_election(partition: Partition):
    pass