from gerrychain import Partition
from ..modules.election import run_statewide_district_elections
from ..modules.mmd_seed_generation import gen_mmd_configs, gen_mmd_seed_partition
from ..modules.ensemble_generation import gen_random_map
from ..modules.plotting import plot_partition
from ..modules.voting_models import party_line_voting
import logging
import consts
from ..modules.load_state_data import load_smd_partition
import run_config
from pprint import pprint
from ..custom_types import VMDPartition
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("starting main method")

    smd_partition: VMDPartition = load_smd_partition(run_config.STATE)
    print(smd_partition)
    return
    mmd_config: dict[int, int] = gen_mmd_configs(len(smd_partition.parts))[0] 
    seed_mmd_partition: Partition = gen_mmd_seed_partition(smd_partition, mmd_config)
    rand_partition: Partition = gen_random_map(seed_mmd_partition, mmd_config, run_config.NUM_RECOM_STEPS, run_config.EPSILON)
    plot_partition(rand_partition, prs=None, district_reps=mmd_config, cmap=consts.DISTINCT_COLORS, show=True)
    pprint(run_statewide_district_elections(rand_partition, mmd_config, party_line_voting))

    
if __name__ == "__main__":
    main()