from gerrychain import Graph, Partition
from geopandas import GeoSeries
import os
import consts
from pathlib import Path
import run_config
from ..custom_types import VMDPartition, ElectionsResults, Ensemble
from gerrychain.updaters import Tally, cut_edges
import logging
logger = logging.getLogger(__name__)
from .ensemble_generation import gen_ensemble
import json
import jsonpickle

"""
This module contains various methods for formatting data.

The state data I used originated from the Redistricting Data Hub, 2016 and 2020
VEST data, and the 2020 Census Bureau Block Group Level. Big thanks to Brendan Fogg
for providing me his formatted .pickle files for each state
containing a GerrychainConfig class defined here:
https://gitlab.com/stony-brook-politech/gilvir-cse416/-/blob/main/redist/algorithm.py

From these serialized GerryChainConfig .pickle files, the gerrychain Graph
stored in GerryChainConfig.graph was extracted and serialized to a .json file
using the gerrychain.Graph.to_json() method. The geometries were extracted from
the 'geometry' column of the GerryChainConfig.underlying_data.precinct_df
GeoDataFrame field into a GeoSeries, and then to a .gpkg file using the
GeoSeries.to_file() method. The graph and geometries can be deserialized into
the original GeoSeries and gerrychain.Graph using the
gerrychain.Graph.from_json() and the GeoSeries.from_file() methods,
respectively.

Each uniquely partitioned map (seed district or element of an ensemble) is
stored in a serialized VMDPartition .json file containing only the assignment
dict and the district_reps dict. This data, during runtime, is combined with the
data from the Graph and GeoSeries files for that state to obtain a VMDPartition.
This arrangement stores the minimal amount of information per random map and
reduces redundancy of copying state data that never changes.

The reason that the Graph and GeoSeries files are separate and not just saved as
one large file is because there is no file format that I could get working that
contains both info in one. In addition, in many instances, the large and
slow-to-load GeoSeries files aren't even needed when there is nothing to
display. 

To support the above serialization scheme, this module assumes a specific directory structure that contains the source gerrychain Graph and in the .json and .gpkg formats as described above,
as well as the generated seed districts, ensembles in the serialized VMDPartition format, and election results.
"""


def gen_smd_seeds() -> None: 
    """
    Generates first serialized VMDPartition .json files by taking the
    original Graph and saving their seed .jsons. Walks through each state
    directory and saves seed to seeds directory.
    """

    state_subdirnames: list[str] = [ f.path for f in os.scandir(consts.STATE_DATA_BASE_DIR) if f.is_dir() ]
    for state_dirname in state_subdirnames:
        prec_graph: Graph = Graph.from_json(os.path.join(consts.STATE_DIR(state_dirname), consts.STATE_GRAPH_FILENAME)) 
        n_districts: int = len(Partition(graph=prec_graph, assignment=consts.DISTRICT_NO_COL).parts) # find a cleaner way of counting the number of districts
        partition: VMDPartition = VMDPartition(graph=prec_graph, assignment=consts.DISTRICT_NO_COL, district_reps=dict.fromkeys(range(1, n_districts+1), 1), seed_type="actual", updaters={consts.CUT_EDGE_UPDATER: cut_edges, consts.POP_UPDATER: Tally(consts.POP_COL, consts.POP_UPDATER)})
        os.makedirs(consts.SMD_SEEDS_DIR(state_dirname), exist_ok=True)
        partition.to_file(consts.SMD_SEEDS_DIR(state_dirname), "actual") 