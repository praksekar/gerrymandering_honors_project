import gerrychain
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
ASSIGNMENT_COL = "CD_2011"
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


def get_district_centroids(district_geo_df: GeoDataFrame) -> dict[int, tuple]:
    district_centroids = {}
    for idx, row in district_geo_df.iterrows():
        district_centroids[idx] = tuple(row["geometry"].centroid.coords)[0]
    return district_centroids


def gen_district_graph(partition: Partition) -> nx.Graph:
    edgelist = []
    for edge in partition["cut_edges"]:
        edgelist.append(
            (partition.assignment[edge[0]], partition.assignment[edge[1]]))
    return nx.Graph(edgelist)


def merge_smds_to_mmds(smd_partition: Partition, config: tuple) -> Partition:
    return


def main() -> None:
    precinct_geo_df: GeoDataFrame = gp.read_file(SHAPE_FILE)
    district_geo_df: GeoDataFrame = precinct_geo_df.dissolve(by=ASSIGNMENT_COL)
    precinct_graph: gerrychain.Graph = Graph.from_json(GRAPH_FILE)
    smd_partition: Partition = Partition(
        precinct_graph, assignment=ASSIGNMENT_COL)
    district_graph: nx.Graph = gen_district_graph(smd_partition)
    district_centroids: dict[int, tuple] = get_district_centroids(
        district_geo_df)
    plot_partition(smd_partition, precinct_geo_df, COLORS)
    nx.draw(district_graph, pos=district_centroids)
    plt.show()


if __name__ == "__main__":
    main()
