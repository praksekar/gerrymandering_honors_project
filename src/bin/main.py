from pathlib import Path
import os
from linetimer import linetimer, CodeTimer
from gerrychain import Partition
from ..modules.election import run_statewide_district_elections_on_map, multi_seat_ranked_choice_tabulation, run_many_statewide_elections_on_ensemble, single_seat_plurality_tabulation
from ..modules.mmd_seed_generation import gen_mmd_seed_partition, pick_HR_3863_desired_mmd_config, pick_max_districts_config
from ..modules.ensemble_generation import gen_ensemble
from ..modules.plotting import plot_partition, plot_ensemble, plot_party_split
from ..modules.voting_models import party_line_voting_comparator
import logging
import consts
from ..modules.data_processing import gen_smd_seeds, gen_mmd_seeds, gen_smd_ensembles, gen_mmd_ensembles, run_election
import run_config
from pprint import pprint
from ..custom_types import VMDPartition, RepsPerDistrict, ElectionsResults, Ensemble
logging.basicConfig(level=run_config.LOGGING_LEVEL)
logger = logging.getLogger(__name__)
logging.getLogger("fiona").setLevel(logging.WARNING)


@linetimer(name=f"running main method", logger_func=logger.info)
def main() -> None:
    logger.info("starting main method")
    # test()
    # format_data()
    # gen_seeds()
    # gen_smd_ensemble("AL")
    # a = consts.SMD_SEEDS_DIRPATH("AL") / "actual"
    # graph = consts.STATE_GRAPH_FILEPATH("AL")
    # geoms = consts.STATE_GEOMETRY_FILEPATH("AL")
    # plot_partition(VMDPartition.from_file(a, graph, geoms), consts.DISTINCT_COLORS, show=True)
    # gen_seeds()
    # load_map(consts.SMD_SEEDS_DIRPATH("AL") / "actual")
    # load_ensemble("AL")
    states = ["NY"] #"NC", "FL", "PA", "MD", "LA", "GA"]
    # time_worker_amounts()
    # gen_smd_seeds(states)
    # gen_mmd_seeds(pick_HR_3863_desired_mmd_config, states)
    # gen_smd_ensembles(100, 10, 0.01, "actual", [], states, 6)
    run_election(consts.SMD_ENSEMBLE_DIRPATH("NY") / "actual-100-[]-1000-0.01", party_line_voting_comparator, single_seat_plurality_tabulation, 6, "NY")
    electionsresults = ElectionsResults.from_file(consts.ELECTIONSRESULTS_DIRPATH("NY") / "actual-10-[]-10-0.01-party_line_voting_comparator-single_seat_plurality_tabulation")
    plot_party_split(electionsresults, 26, consts.PLOT_DIRPATH / (consts.ELECTIONSRESULTS_FILENAME(electionsresults) + ".png"))
    # plot_ensemble(Ensemble.from_file(consts.MMD_ENSEMBLE_DIRPATH("NY") / "pick_HR_3863_desired_mmd_config-10-[]-10-0.01", load_geoms=True), show=True)
    return

    # smd_partition: VMDPartition = load_smd_partition(run_config.STATE)
    # seed_mmd_partition: Partition = gen_mmd_seed_partition(smd_partition, pick_HR_3863_desired_mmd_config)
    # rand_mmd_partition: Partition = gen_random_map(seed_mmd_partition, run_config.SMD_NUM_RECOM_STEPS, run_config.EPSILON)
    # print(f"smd_partition: {smd_partition}")
    # rand_smd_partition: Partition = gen_random_map(smd_partition, run_config.NUM_RECOM_STEPS, run_config.EPSILON)
    # rand_mmd_partition: Partition = gen_random_map(seed_mmd_partition, run_config.NUM_RECOM_STEPS, run_config.EPSILON)
    plot_partition(rand_mmd_partition, prs=None, cmap=consts.DISTINCT_COLORS, show=True)
    # plot_partition(rand_smd_partition, prs=None, cmap=consts.DISTINCT_COLORS, show=True)
    # pprint(run_statewide_district_elections(rand_partition, mmd_config, party_line_voting))

def time_worker_amounts() -> None:
    states = ["NY"]
    workers_nums = [7, 14, 28, 35]
    for workers in workers_nums:
        with CodeTimer(f"{workers} workers", logger_func=logger.debug):
            gen_smd_ensembles(100, 100, 0.01, "actual", [], states, workers)
            gen_mmd_ensembles(100, 100, 0.01, "pick_HR_3863_desired_mmd_config", [], states, workers)

def test() -> None:
    print(consts.MMD_SEEDS_DIRPATH("NY"))
    return
    # seed_smd_partition: VMDPartition = load_smd_partition(run_config.STATE)

    # smd_ensemble: list[VMDPartition] = gen_ensemble(seed_smd_partition, run_config.SMD_NUM_RECOM_STEPS, run_config.SMD_ENSEMBLE_SIZE, run_config.SMD_EPSILON)
    # smd_election_results: ElectionsResults = run_many_statewide_elections_on_ensemble(smd_ensemble, run_config.VOTING_MODEL, single_seat_plurality_tabulation)
    # print(smd_election_results)

    # seed_mmd_partition: VMDPartition = gen_mmd_seed_partition(seed_smd_partition, run_config.MMD_CONFIG_CHOOSER)
    # mmd_ensemble: list[VMDPartition] = gen_ensemble(seed_mmd_partition, run_config.MMD_NUM_RECOM_STEPS, run_config.MMD_ENSEMBLE_SIZE, run_config.MMD_EPSILON)
    # mmd_election_results: ElectionsResults = run_many_statewide_elections_on_ensemble(mmd_ensemble, run_config.VOTING_MODEL, multi_seat_ranked_choice_tabulation)
    # print(mmd_election_results)

# def format_data() -> None:
#     generate_and_save_smd_ensemble("AL")
    # save_actual_state_district_as_seed_assignment_dict()
    # partition: VMDPartition = VMDPartition.fromJSON(os.path.join(consts.STATE_DATA_BASE_DIR, "AL", "smd_seeds", "2020_PRES"), "AL", load_geometries=True)
    # plot_partition(partition, prs=None, cmap=consts.DISTINCT_COLORS, show=True)

def load_map(path: Path):
    map: VMDPartition = VMDPartition.from_file(path, load_geoms=True)
    plot_partition(map, consts.DISTINCT_COLORS, show=True)


def gen_seeds() -> None:
    gen_smd_seeds()


def gen_smd_ensemble(state: str) -> None:
    json_file_path: Path = consts.SMD_SEEDS_DIRPATH(state) / "actual"
    #seed: VMDPartition = VMDPartition.from_file(json_file_path, consts.STATE_GRAPH_PATH(state), consts.STATE_GEOMETRY_PATH(state))
    seed: VMDPartition = VMDPartition.from_file(json_file_path)
    ensemble: Ensemble = gen_ensemble(seed, 10, 10, 0.01, "aaa", [])
    ensemble.to_file(consts.SMD_ENSEMBLE_DIRPATH(state) / consts.SMD_ENSEMBLE_FILENAME(ensemble))


def load_ensemble(state: str) -> None:
    epath = consts.SMD_ENSEMBLE_DIRPATH("AL") / "SMD-aaa-[]-10-0.01"
    e = Ensemble.from_file(epath, load_geoms=True)
    for map in e.maps:
        plot_partition(map, consts.DISTINCT_COLORS, show=True)


if __name__ == "__main__":
    main()