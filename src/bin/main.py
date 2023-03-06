from __future__ import annotations
from gerrychain import Partition
from pptx import Presentation
import itertools
flatten = itertools.chain.from_iterable
from ..modules.election import run_statewide_district_elections
from ..modules.mmd_seed_generation import gen_mmd_configs, gen_mmd_seed_assignment
from ..modules.ensemble_generation import mmd_recom, gen_random_map
from ..modules.plotting import plot_partition
from ..modules.voting_models import party_line_voting
import logging
import consts
from ..modules.mmd_seed_generation import gen_mmd_seed_partition
from state_configs import load_state_data
import run_config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





def main() -> None:
    logger.info("starting main method")

    smd_partition: Partition = load_state_data(run_config.STATE)
    mmd_config: dict[int, int] = gen_mmd_configs(len(smd_partition.parts))[0] 
    seed_mmd_partition: Partition = gen_mmd_seed_partition(smd_partition, mmd_config)
    rand_partition: Partition = gen_random_map(seed_mmd_partition, mmd_config, run_config.NUM_RECOM_STEPS, run_config.EPSILON)
    plot_partition(rand_partition, prs=None, district_reps=mmd_config, cmap=consts.DISTINCT_COLORS, show=True)
    print(run_statewide_district_elections(rand_partition, mmd_config, party_line_voting))

    


if __name__ == "__main__":
    main()