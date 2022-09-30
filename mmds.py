import gerrychain
from gerrychain.accept import always_accept
from functools import partial
import random
from gerrychain import constraints, Graph, Partition, MarkovChain
from gerrychain.updaters import cut_edges, Tally
from gerrychain.tree import random_spanning_tree
import geopandas as gp
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from geopandas import GeoSeries
import networkx as nx


SHAPE_FILE = "./state_data/PA/PA.shp"
GRAPH_FILE = "./PAjson_wo_geometry"
ASSIGNMENT_COL = "CD_2011"
MARKOV_CHAIN_STEPS = 10
POP_COL = "TOTPOP"
COLORS = ListedColormap(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
'#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff',
'#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075',
'#808080'])


def plot_partition(partition: Partition, precinct_geometries: GeoSeries, cmap=COLORS):
    partition.plot(precinct_geometries, cmap=cmap)
    centroids : dict[tuple] = get_district_centroids(partition, precinct_geometries)
    total_pop = get_total_pop(partition)
    for partID, coord in centroids.items():
        pop_frac = float(partition["population"][partID]/total_pop) * 18
        plt.text(coord[0], coord[1], "District %d\nPopulation: %d\nPop Frac: %3f/18" % (partID, partition["population"][partID], pop_frac))
    print("total population: %d" % total_pop)
    plt.show()
    plt.clf()


def split_graph(graph: nx.Graph, partIDs: tuple, graph_pop: int, pop_target: int, epsilon: float, cut_iterations: int = 100, node_repeats: int = 100) -> dict[int, int]:
    print("graph node = " + str(graph.nodes))
    for i in range(node_repeats):
        spanning_tree = random_spanning_tree(graph)
        random_edges_left = set(spanning_tree.edges)
        print("spanning tree type = " + str(type(spanning_tree)))
        print("spanning_tree edges = " + str(type(spanning_tree.edges)))
        min_pop = pop_target * (1 - epsilon)
        print("min_pop = " + str(min_pop))
        max_pop = pop_target * (1 + epsilon)
        print("max_pop = " + str(max_pop))
        max_pop_complement = graph_pop - min_pop
        min_pop_complement = graph_pop - max_pop
        for j in range(cut_iterations):
            random_edge = random.choice(list(random_edges_left))
            spanning_tree.remove_edge(random_edge[0], random_edge[1])
            pop_sum = 0
            components = [c for c in nx.connected_components(spanning_tree)]
            for nodeID in components[0]:
                pop_sum += int(graph.nodes[nodeID][POP_COL])
            print("num_components = %d, node repeat = %d, cut iteration = %d, \
            pop_sum of component = %d, num_nodes in component 1: %d, num_nodes in component 2: %d, random_edge = \
            %s, min_pop = %d, max_pop = %d" % (len(components), i, j, pop_sum, \
            len(components[0]), len(components[1]), str(random_edge), min_pop, max_pop))
            if (pop_sum > min_pop and pop_sum < max_pop) or (pop_sum > min_pop_complement and pop_sum < max_pop_complement):
                flips = {}
                for idx, component in enumerate(components):
                    for nodeID in component:
                        flips[nodeID] = partIDs[idx]
                return flips
            spanning_tree.add_edge(random_edge[0], random_edge[1])
            random_edges_left.remove(random_edge)
    raise Exception("partitioning failed after %d random cut iterations after %d node repeats" % (cut_iterations, node_repeats))


def mmd_recom(partition: Partition):
    edge = random.choice(tuple(partition["cut_edges"]))
    parts_to_merge = (partition.assignment.mapping[edge[0]], partition.assignment.mapping[edge[1]])
    subgraph = partition.graph.subgraph(
        partition.parts[parts_to_merge[0]] | partition.parts[parts_to_merge[1]]
    )
    subgraph_pop = partition["population"][parts_to_merge[0]] + partition["population"][parts_to_merge[1]] 
    pop_target = partition["population"][parts_to_merge[0]] 
    flips = split_graph(graph=subgraph.graph, partIDs=parts_to_merge, graph_pop=subgraph_pop, pop_target=pop_target, epsilon=0.1)
    return partition.flip(flips)


def get_total_pop(partition: Partition, pop_col=POP_COL):
    total_pop = 0
    for partID, nodeIDs in partition.parts.items():
        for nodeID in nodeIDs:
            total_pop += int(partition.graph.nodes[nodeID][pop_col])
    return total_pop


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
            spanning_tree.remove_edges_from(random_edges)
            sizes = [len(component) for component in nx.connected_components(spanning_tree)]
            if sizes.count(3) == component_sizes[0] and sizes.count(4) == component_sizes[1] and sizes.count(5) == component_sizes[2]:
                return spanning_tree
            spanning_tree.add_edges_from(random_edges)
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
    mmd_configs: list[tuple] = gen_mmd_configs(smd_partition)
    print(mmd_configs)
    district_partition = partition_district_graph(smd_graph, mmd_configs[2])
    # for mmd_config in mmd_configs:
    #     print("showing district config: %s" % str(mmd_config))
        # district_partition = partition_district_graph(smd_graph, mmd_config)
    mmd_partition = Partition(
        precinct_graph, 
        assignment=gen_mmd_assignment(smd_partition, district_partition),
        updaters={"cut_edges": cut_edges, "population": Tally(POP_COL, "population")} 
    )

    proposal = partial(mmd_recom)

    pop_constraint = constraints.within_percent_of_ideal_population(mmd_partition, 0.5)

    chain = MarkovChain(
        proposal=proposal,
        constraints=[pop_constraint],
        accept=always_accept,
        initial_state=mmd_partition,
        total_steps=MARKOV_CHAIN_STEPS
    )

    # nx.draw(district_partition, pos=get_district_centroids(smd_partition, precinct_geometries))
    for partition in chain:
        plot_partition(partition, precinct_geometries)


if __name__ == "__main__":
    main()