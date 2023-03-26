import json
import sys
from mpi4py import MPI
import pickle
from gerrychain.random import random
from redist.algorithm import GerryChainConfig, get_chain, run_chain

from redist.postprocessing import RedistrictingPlan
from gerrychain import Partition

import geopandas as gpd
import pandas as pd

COMMUNICATOR = MPI.COMM_WORLD

"""
Originally Written for Gilvir's CSE 416 Project
A simple script that injects an environment variable EP_TASK_ID 
from 0 through N, where N is specified
"""


if __name__ == "__main__":
    '''
    Case: Rank 0 / Lead Process
    '''
    jobs_per_process = None
    args = sys.argv
    start, end = int(sys.argv[1]), int(sys.argv[2])
    config_pickle_filename = sys.argv[3]
    state_name = config_pickle_filename.split(".")[0]
    if COMMUNICATOR.Get_rank() == 0:
        jobs = list(range(start, end))
        num_proccesses = COMMUNICATOR.size
        jobs_per_process = [
            jobs[i::num_proccesses]
            for i in range(num_proccesses)
        ]
    #
    allocated_jobs = COMMUNICATOR.scatter(jobs_per_process)
    config: GerryChainConfig = None
    initial_part: Partition = None
    with open(config_pickle_filename, "rb") as f:
        config, initial_part = pickle.load(f)
    data = config.underlying_data

    for job in allocated_jobs:
        print(f"Job: {job} Rank: {COMMUNICATOR.Get_rank()}")
        random.seed(job)
        chain = get_chain(config, initial_part)
        final_partition = run_chain(config, chain)
        plan = RedistrictingPlan(data, final_partition)
        # output election data
        output_df: gpd.GeoDataFrame = plan.district_df.fillna(0).copy()
        output_df["area"] = output_df.geometry.area
        output_df["perimeter"] = output_df.geometry.boundary.length
        # TODO - figure out name deserialization on the other side
        output_df = output_df.rename(columns=str)
        # TODO - see if a faster serialization scheme can be created
        # for now - dont worry about it
        # with open(f"output/pickle/{state_name}_{job}.pickle", "wb") as f:
        #     pickle.dump((plan.district_df, plan.precinct_district_map), f)

        # TODO - figure out better geojson storage mechanism.
        # output_df.to_file(
        #     f"output/geojson/{state_name}_{job}.geojson", 
        #     driver="GeoJSON"
        # )
        # output election data csvs
        pd.DataFrame(
            output_df.drop(columns=["geometry"])
        ).to_csv(f"output/csv/{state_name}_{job}.csv")
        # output precinct district maps:
        with open(f"output/pdm/{state_name}_{job}_PDM.json", "w") as f:
            json.dump({
                str(p_id): str(d_id)
                for p_id, d_id in plan.precinct_district_map.items()
            }, f)
