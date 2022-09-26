from gerrychain import Graph, Partition, MarkovChain
import geopandas as gp
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from gerrychain.tree import recursive_tree_part
from geopandas import GeoDataFrame
import networkx as nx

SHAPE_FILE = "./state_data/PA/PA.shp"
GRAPH_FILE = "./PAjson_wo_geometry"
COLORS = ListedColormap(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080',
                         '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#000000'])


def plot_partition(partition: Partition, geometries: GeoDataFrame, colors: ListedColormap) -> None:
    partition.plot(geometries, cmap=colors)


def gen_mmd_configs(smd_partition: Partition) -> list[tuple]:
    n_reps = len(smd_partition.parts)
    configs = []
    for x1 in range(n_reps//3+1):
        for x2 in range(n_reps//4+1):
            for x3 in range(n_reps//5+1):
                if x1*3 + x2*4 + x3*5 == n_reps:
                    configs.append((x1, x2, x3))
    return configs


def merge_smds_to_mmds(smd_partition: Partition, config: tuple) -> Partition:
    return


def reduce_partition_to_district_graph(partition: Partition) -> nx.Graph:
    edgelist = []
    for edge in partition["cut_edges"]:
        edgelist.append(
            (partition.assignment[edge[0]], partition.assignment[edge[1]]))
    return nx.Graph(edgelist)


def main() -> None:
    geo_df: GeoDataFrame = gp.read_file(SHAPE_FILE)
    print(geo_df.columns)
    graph: Graph = Graph.from_json(GRAPH_FILE)
    smd_partition: Partition = Partition(
        graph,
        assignment="CD_2011"
    )
    print(reduce_partition_to_district_graph(smd_partition))


if __name__ == "__main__":
    main()
