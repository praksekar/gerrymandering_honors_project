from gerrychain import Partition
from ..modules.election import run_statewide_district_elections_on_map, multi_seat_ranked_choice_tabulation, run_many_statewide_elections_on_ensemble, single_seat_plurality_tabulation
from ..modules.mmd_seed_generation import gen_mmd_seed_partition, pick_HR_3863_desired_mmd_config, pick_max_districts_config
from ..modules.ensemble_generation import gen_ensemble
from ..modules.plotting import plot_partition
from ..modules.voting_models import party_line_voting_comparator
import logging
import consts
from ..modules.data_processing import gen_smd_seeds
import run_config
from pprint import pprint
from ..custom_types import VMDPartition, RepsPerDistrict, ElectionsResults, Ensemble
logging.basicConfig(level=run_config.LOGGING_LEVEL)
logger = logging.getLogger(__name__)
logging.getLogger("fiona").setLevel(logging.WARNING)
import os
from pathlib import Path



def main() -> None:
    logger.info("starting main method")
    test()
    # format_data()
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

def test() -> None:
    print(consts.MMD_SEEDS_DIR("NY"))
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

def gen_seeds() -> None:
    gen_smd_seeds() 

def gen_smd_ensemble(state: str) -> None:
    json_file_path: Path = os.path.join(consts.SMD_ENSEMBLE_DIR, "actual")
    seed: VMDPartition = VMDPartition.from_file(json_file_path, consts.STATE_GRAPH_PATH(state), consts.STATE_GEOMETRY_PATH)
    ensemble: Ensemble = gen_ensemble(seed, 10, 10, 0.01, "aaa", [])
    ensemble.to_file(os.path.join(consts.SMD_ENSEMBLE_DIR(state), consts. SMD_ENSEMBLE_FILENAME(ensemble)))


    
    
if __name__ == "__main__":
    main()