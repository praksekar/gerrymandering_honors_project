from gerrychain import Partition
from statistics import mode
from linetimer import CodeTimer, linetimer
from ..custom_types import VotingComparator, VMDPartition, RepsPerDistrict, Precinct, Voter, Party, ElectionsResults
import run_config
import logging
from functools import partial, cmp_to_key
import consts
from pprint import pprint
from .utils import round_up, round_down
logger = logging.getLogger(__name__)
from ..custom_types import Ballot, Candidate, Party, Tabulator, Ensemble
import itertools
flatten = itertools.chain.from_iterable
from multiprocessing import Pool


# @linetimer(name=f"running multi seat ranked choice tabulation", logger_func=logger.debug)
def multi_seat_ranked_choice_tabulation(ballots: list[Ballot], candidates: set[Candidate], n_winners: int) -> list[Candidate]:
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

    tabulation_round = 1
    continuing_candidates: set[Candidate] = candidates.copy()
    winners: set[Candidate] = set()
    multi_seat_threshold: float = round_up(len(ballots)/(1+n_winners), 4)
    logger.debug(f"multi seat threshold: {multi_seat_threshold}")

    while len(continuing_candidates) + len(winners) > n_winners:
        tabulation_round += 1
        # first, perform vote tabulation for this round and find candidates that exceed threshold
        tally: dict[Candidate, float] = {c:0 for c in continuing_candidates} # initializing votes of all continuing candidates to 0
        for ballot in ballots: 
            tally[ballot.curr_choice()] += ballot.weight
        logger.debug(f"current tally: {tally}")
        above_threshold_candidates: set[Candidate] = {c for c, v in tally.items() if v > multi_seat_threshold}

        # do surplus tabulation round if there are candidates above threshold
        if len(above_threshold_candidates) > 0: 
            logger.debug("surplus tabulation round")
            winners = winners | above_threshold_candidates # all candidates above the threshold are immediately declared as winners and added to the winners set
            continuing_candidates -= above_threshold_candidates # the winners are no longer considered as continuing candidates
            # perform the vote transfer process for each candidate with a vote count higher than the threshold
            for above_threshold_candidate in above_threshold_candidates: 
                logger.debug(f"transferring votes for above threshold candidate: {above_threshold_candidates}")
                candidate_votes: float = tally[above_threshold_candidate]
                surplus_fraction: float = (candidate_votes-multi_seat_threshold)/candidate_votes
                # iterate through ballots for which the current above_threshold_candidate is the current choice.
                # for each such ballot, multiply its weight by the surplus fraction and then set its current choice to the next continuing candidate on that ballot.
                for ballot in ballots: 
                    if ballot.curr_choice() == above_threshold_candidate and not ballot.was_transferred: # select above threshold ballots that have not already been transferred in this round
                        ballot.weight = round_down(ballot.weight*surplus_fraction, 4)
                        ballot.next_continuing_choice(continuing_candidates)
                        ballot.was_transferred = True # this ballot needs to be marked as transferred so we don't accidentally transfer it again in the next iteration
            for ballot in ballots: # reset each ballot as not transferred for the next round of counting
                ballot.was_transferred = False 

        # otherwise, if there are no candidates above threshold, this is a candidate elimination round
        else: 
            min_candidate: Candidate = min(tally, key=tally.get) 
            logger.debug(f"candidate elimination round, removing {min_candidate}")
            continuing_candidates.remove(min_candidate) # remove candidate with the minimum votes
            # transfer each ballot for which the candidate was the current choice to the next continuing candidate on that ballot
            for ballot in ballots: 
                if ballot.curr_choice() == min_candidate:
                    ballot.next_continuing_choice(continuing_candidates)                    

    # if we reach here, it means that the number of winners + continuing candidates is <= the number of required seats. So, return all of the winners and continuing candidates.
    return list(winners | continuing_candidates)


# @linetimer(name=f"running single seat plurality tabulation", logger_func=logger.debug)
def single_seat_plurality_tabulation(ballots: list[Ballot], candidates: set[Candidate], n_winners: int) -> list[Candidate]:
    return [mode([b.curr_choice() for b in ballots])]


# @linetimer(name=f"generating candidates", logger_func=logger.debug)
def gen_candidates(n_seats: int, districtID: int) -> set[Candidate]: 
    """
    Generates a list of n_seats candidates from each party. This can be used for
    both SMD and MMD districts, as the number of candidates from each party is
    equal to the number of districts (general case in SEC. 203 of H.R. 3863).

    Arguments:
        n_seats: number of seats to be filled
    Returns:
        set of candidates being considered in a district
    """

    candidates: set[Candidate] = set()
    candidate_counter: int = 1
    for party in Party:
        for _ in range(n_seats):
            candidates.add(Candidate(party, "Candidate %d" % candidate_counter, districtID, 1))
            candidate_counter += 1
    return candidates


def get_prec_voters(precinct: Precinct) -> list[Voter]:
    return [Voter(Party.DEMOCRAT)]*int(precinct[run_config.DEM_VOTE_TALLY_COL]) + [Voter(Party.REPUBLICAN)]*int(precinct[run_config.REP_VOTE_TALLY_COL])


def get_district_voters(partition: VMDPartition, districtID: int) -> list[Voter]:
    with CodeTimer(name=f"getting voters from district {districtID}", logger_func=logger.debug):
        return list(flatten([get_prec_voters(partition.graph.nodes[p]) for p in partition.parts[districtID]]))


def voter_to_ballot(voter: Voter, candidates: list[Candidate], voting_model: VotingComparator) -> Ballot:
    return Ballot(sorted(candidates, key=cmp_to_key(partial(voting_model, voter=voter))))


def district_voters_to_ballots(voters: list[Voter], candidates: list[Candidate], voting_model: VotingComparator) -> list[Ballot]:
    with CodeTimer(name=f"getting ballots from {len(voters)} voters using {voting_model.__name__}", logger_func=logger.debug):
       district_ballots: list[Ballot] = [voter_to_ballot(v, candidates, voting_model) for v in voters]
    logger.debug(f"first 3 district ballots: {district_ballots[:3]}, last 3 district ballots: {district_ballots[-3:]}")
    return district_ballots


def run_district_election(partition: VMDPartition, districtID: int, voting_model: VotingComparator, tabulator: Tabulator) -> list[Candidate]:
    with CodeTimer(f"running election on district {districtID}", logger_func=logger.debug):
        candidates: list[Candidate] = gen_candidates(partition.district_reps[districtID], districtID)
        voters: list[Voter] = get_district_voters(partition, districtID)
        ballots: list[Ballot] = district_voters_to_ballots(voters, candidates, voting_model)
        winners: list[Candidate] = tabulator(ballots, candidates, partition.district_reps[districtID])
        logger.debug(f"district {districtID} winners: {winners}")
        return winners


def run_statewide_district_elections_on_map(partition: VMDPartition, map_idx: int, voting_model: VotingComparator, tabulator: Tabulator) -> list[Candidate]:
    logger.info(f"running district elections on ensemble map {map_idx}")
    winners: list[Candidate] = list(flatten([run_district_election(partition, p, voting_model, tabulator) for p in sorted(partition.parts.keys())]))
    logger.debug(f"state winners: {winners}")
    return winners


def run_many_statewide_elections_on_ensemble(ensemble: list[Partition], voting_model: VotingComparator, tabulator: Tabulator) -> ElectionsResults: 
    return [run_statewide_district_elections_on_map(m, i, voting_model, tabulator) for i, m in enumerate(ensemble)]
    
def run_statewide_district_elections_on_map_parallel(partition: dict, map_idx: int, voting_model: VotingComparator, tabulator: Tabulator) -> list[Candidate]:
    partition = VMDPartition.from_json_dict(partition)
    logger.info(f"running district elections on ensemble map {map_idx}")
    winners: list[Candidate] = list(flatten([run_district_election(partition, p, voting_model, tabulator) for p in sorted(partition.parts.keys())]))
    logger.debug(f"state winners: {winners}")
    return winners

def run_many_statewide_elections_on_ensemble_parallel(ensemble: Ensemble, voting_model: VotingComparator, tabulator: Tabulator, n_workers: int) -> ElectionsResults: 
    args = []
    for i in range(len(ensemble.maps)):
        args.append((ensemble.maps[i].to_json_dict(), i, voting_model, tabulator))
    with Pool(n_workers) as p:
        results = p.starmap(run_statewide_district_elections_on_map_parallel, args)
    return ElectionsResults(results, voting_model.__name__, consts.ENSEMBLE_FILENAME(ensemble), tabulator.__name__)