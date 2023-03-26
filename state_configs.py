from gerrychain import Graph, Partition
from geopandas import GeoSeries
import os
import consts
from pathlib import Path
from bin.modules.custom_types import VMDPartition


def load_smd_partition(state: str) -> Partition:
    state_data_dir: Path = os.path.join(consts.STATE_DATA_BASE_DIR, state)
    prec_graph: Graph = Graph.from_json(os.path.join(state_data_dir, consts.STATE_GRAPH_FILENAME)) 
    print(prec_graph.nodes[0])
    prec_geometries: GeoSeries = GeoSeries.from_file(os.path.join(state_data_dir, consts.STATE_GEOMETRY_FILENAME)) 
    prec_graph.geometry = prec_geometries
    n_districts = len(Partition(graph=prec_graph, assignment=consts.DISTRICT_NO_COL).parts) # find a cleaner way of counting the number of districts
    return VMDPartition(dict.fromkeys(range(1, n_districts+1), 1))



def serialize_state_data(graph, path):
    pass