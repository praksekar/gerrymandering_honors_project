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


def reduce_partition_to_district_graph(partition: Partition, geo_df: GeoDataFrame) -> nx.Graph:
    G: nx.Graph = nx.Graph()
    # district_geo_df = geo_df.dissolve(by="CD_2011", as_index=True)
    G.add_nodes_from(partition.parts)
    # pos = {}
    # for part in partition.parts:
    #     pos[part] = tuple(district_geo_df.geometry[part].centroid.coords)[0]
    for edge in partition["cut_edges"]:
        G.add_edge(
            partition.assignment[edge[0]], partition.assignment[edge[1]])
    # plot_partition(partition, district_geo_df, COLORS)
    return G


def


def main() -> None:
    geo_df: GeoDataFrame = gp.read_file(SHAPE_FILE)
    print(geo_df.columns)
    graph: Graph = Graph.from_json(GRAPH_FILE)
    smd_partition: Partition = Partition(
        graph,
        assignment="CD_2011"
    )
    reduce_partition_to_district_graph(smd_partition, geo_df)


if __name__ == "__main__":
    main()
