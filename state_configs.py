from gerrychain import Graph, Partition
from geopandas import GeoSeries
import os
import consts
from pathlib import Path


def load_state_data(state: str) -> Partition:
    state_data_dir: Path = os.path.join(consts.STATE_DATA_BASE_DIR, state)
    prec_graph: Graph = Graph.from_json(os.path.join(state_data_dir, consts.STATE_GRAPH_FILENAME)) 
    prec_geometries: GeoSeries = GeoSeries.from_file(os.path.join(state_data_dir, consts.STATE_GEOMETRY_FILENAME)) 
    prec_graph.geometry = prec_geometries
    return Partition(graph=prec_graph, assignment=consts.DISTRICT_NO_COL)



def serialize_state_data(graph, path):
    pass