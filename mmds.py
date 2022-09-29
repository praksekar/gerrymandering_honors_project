import gerrychain
import random
from gerrychain import Graph, Partition, MarkovChain
import geopandas as gp
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from geopandas import GeoSeries
import networkx as nx

SHAPE_FILE = "./state_data/PA/PA.shp"
GRAPH_FILE = "./PAjson_wo_geometry"
ASSIGNMENT_COL = "CD_2011"
POP_COL = "TOTPOP"
COLORS = ListedColormap(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
'#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff',
'#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075',
'#808080'])


def plot_partition(partition: Partition, precinct_geometries: GeoSeries, cmap=COLORS):
    partition.plot(precinct_geometries, cmap=COLORS)
    centroids : dict[tuple] = get_district_centroids(partition, precinct_geometries)
    populations = {}
    total_pop = 0
    for partID, nodeIDs in partition.parts.items():
        part_pop = 0
        for nodeID in nodeIDs:
            part_pop += int(partition.graph.nodes[nodeID][POP_COL])
        populations[partID] = part_pop
        total_pop += part_pop
    for partID, coord in centroids.items():
        pop_frac = float(populations[partID]/total_pop) * 18
        plt.text(coord[0], coord[1], "District %d\nPopulation: %d\nPop Frac: %3f/18" % (partID, populations[partID], pop_frac))
    print("total population: %d" % total_pop)
    plt.show()
    plt.clf()


def gen_mmd_configs(smd_partition: Partition) -> list[tuple]:
    n_reps = len(smd_partition.parts)
    configs = []
    for x1 in range(n_reps//3+1):
        for x2 in range(n_reps//4+1):
            for x3 in range(n_reps//5+1):
                if x1*3 + x2*4 + x3*5 == n_reps:
                    configs.append((x1, x2, x3))
    return configs


def get_district_centroids(partition: Partition, precinct_geometries: GeoSeries) -> dict[int, tuple]:
    district_centroids = {}
    for part, nodes in partition.parts.items():
        part_geometries = precinct_geometries.loc[precinct_geometries.index[list(nodes)]]
        district_centroids[part] = tuple(part_geometries.unary_union.centroid.coords)[0]
    return district_centroids


def gen_district_graph(partition: Partition) -> nx.Graph:
    edgelist = []
    for edge in partition["cut_edges"]:
        edgelist.append((partition.assignment[edge[0]], partition.assignment[edge[1]]))
    return nx.Graph(edgelist)


def partition_district_graph(G: nx.Graph, component_sizes: tuple, cut_iterations: int = 100000, node_repeats: int = 5) -> nx.Graph:
    nparts: int = sum(component_sizes)
    for _ in range(node_repeats):
        spanning_tree: nx.Graph = nx.random_spanning_tree(G)
        for _ in range(cut_iterations):
            random_edges: list[tuple] = random.sample(list(spanning_tree.edges), nparts-1)
            cut_spanning_tree: nx.Graph = spanning_tree.copy()
            cut_spanning_tree.remove_edges_from(random_edges)
            sizes = [len(component) for component in nx.connected_components(cut_spanning_tree)]
            if sizes.count(3) == component_sizes[0] and sizes.count(4) == component_sizes[1] and sizes.count(5) == component_sizes[2]:
                return cut_spanning_tree
    raise Exception("partitioning failed after %d random cut iterations after %d node repeats" % (cut_iterations, node_repeats))


def gen_mmd_assignment(smd_partition: Partition, partitioned_district_graph: nx.Graph) -> Partition:
    new_assignment = {}
    district_counter = 0
    for component in nx.connected_components(partitioned_district_graph):
        for part_node in component:
            for precinct_node in smd_partition.parts[part_node]:
                new_assignment[precinct_node] = district_counter
        district_counter += 1
    return new_assignment


def main() -> None:
    precinct_graph: gerrychain.Graph = Graph.from_json(GRAPH_FILE)
    precinct_geometries: GeoSeries = gp.GeoSeries.from_file(SHAPE_FILE)
    smd_partition: Partition = Partition(precinct_graph, assignment=ASSIGNMENT_COL)
    smd_graph: nx.Graph = gen_district_graph(smd_partition)
    # smd_centroids: dict[int, tuple] = get_district_centroids(smd_partition, precinct_geometries)
    mmd_configs: list[tuple] = gen_mmd_configs(smd_partition)
    print(mmd_configs)
    for mmd_config in mmd_configs:
        print("showing district config: %s" % str(mmd_config))
        district_partition = partition_district_graph(smd_graph, mmd_config)
        mmd_partition = Partition(precinct_graph, assignment=gen_mmd_assignment(smd_partition, district_partition))
        plot_partition(mmd_partition, precinct_geometries)


if __name__ == "__main__":
    main()
