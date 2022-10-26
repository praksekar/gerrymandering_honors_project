import random
from disjoint_set import DisjointSet
from linetimer import CodeTimer
import time
from functools import partial
import gerrychain
import matplotlib.pyplot as plt
import networkx as nx
from geopandas import GeoSeries
from gerrychain import Graph, MarkovChain, Partition, constraints
from gerrychain.accept import always_accept
from gerrychain.updaters import Tally, cut_edges
from matplotlib.colors import ListedColormap
from pptx import Presentation
from typing import Callable


SHAPE_FILE = "./state_data/PA/PA.shp"
GRAPH_FILE = "./PAjson_wo_geometry"
PRES_FILE = "./pres_output/mmd_recom2"
SMD_ASSIGNMENT_COL = "CD_2011"
PLOT_INTERVAL = 1 
POP_COL = "TOTPOP"
COLORS = ListedColormap(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
'#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff',
'#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075',
'#808080'])

class MMD_Partition(Partition):
    def __init__(self, graph=None, assignment=None, updaters=None, parent=None, flips=None, use_default_updaters=True):
        super().__init__(self, graph, assignment, updaters, parent, flips, use_default_updaters)
        self.


def add_plot_to_pres(prs):
    plt.savefig("/tmp/graph.png")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture("/tmp/graph.png", 0, 0)
    print("slide added")


def plot_partition(partition: Partition, precinct_geometries: GeoSeries, prs, show=False, cmap=COLORS):
    # plt.title("Markov chain step: %d" % chain_step)
    partition.plot(precinct_geometries, cmap=cmap)
    centroids : dict[int, tuple] = get_district_centroids(partition, precinct_geometries)
    for partID, coord in centroids.items():
        pop_frac = float(partition["population"][partID]/sum(partition["population"].values())) * 18
        plt.text(coord[0], coord[1], "District %d\nPopulation: %d\nPop Frac: %3f/18" % (partID, partition["population"][partID], pop_frac))
    if prs is not None:
        add_plot_to_pres(prs)
    if show:
        plt.show()


def count_components(G: nx.Graph) -> int:
    return len([c for c in nx.connected_components(G)])


def find_cut(graph, tree: Graph, curr_node: int, parent: int, graph_pop: int, pop_rng: tuple) -> tuple:
    sum = graph.nodes[curr_node][POP_COL] 
    for child in tree.neighbors(curr_node):
        if child != parent:
            child_sum, edge_found = find_cut(graph, tree, child, curr_node, graph_pop, pop_rng) 
            if edge_found:
                return (None, edge_found)
            sum += child_sum
    if pop_rng[0] <= sum <= pop_rng[1] or pop_rng[0] <= graph_pop-sum <= pop_rng[1]:
        return (None, (curr_node, parent))
    return (sum, None)


def split_graph_by_pop(graph: nx.Graph, pop_target: int, graph_pop: int, epsilon: float, node_repeats: int = 30) -> tuple[list[int]]:
    pop_rng = (pop_target * (1 - epsilon), pop_target * (1 + epsilon))
    graph_edges = list(graph.edges)
    for i in range(node_repeats):
        with CodeTimer("create spanning tree"):
            spanning_tree = rand_spanning_tree(graph, graph_edges)
        root = random.choice(list(spanning_tree.nodes))
        sum, cut_edge = find_cut(graph, spanning_tree, root, None, graph_pop, pop_rng)
        if cut_edge:
            print("finished recom after %d random spanning trees on %d nodes" % (i+1, len(spanning_tree.nodes)))
            spanning_tree.remove_edge(cut_edge[0], cut_edge[1])
            comp_1 = [node for node in nx.dfs_postorder_nodes(spanning_tree, source=cut_edge[0])]
            comp_2 = [node for node in nx.dfs_postorder_nodes(spanning_tree, source=cut_edge[1])]
            return(comp_1, comp_2)
    raise Exception("partitioning failed")


def rand_spanning_tree(graph: nx.Graph, edges):
    spanning_forest = nx.Graph()
    spanning_forest.add_nodes_from(graph.nodes)
    random.shuffle(edges)
    ds = DisjointSet()
    for node in spanning_forest.nodes:
        ds.find(node)
    for u, v in edges:
        if not ds.connected(u, v):
            spanning_forest.add_edge(u, v)
            ds.union(u, v)
    return spanning_forest

 
def mmd_recom(partition: Partition, epsilon: float) -> Partition:
    edge = random.choice(list(partition["cut_edges"]))
    partIDs = (partition.assignment[edge[0]], partition.assignment[edge[1]])
    print("doing recom on districts %d, %d" % (partIDs[0], partIDs[1]))
    merged_subgraph = partition.graph.subgraph(partition.parts[partIDs[0]] | partition.parts[partIDs[1]])
    print("subgraph components = %d" % count_components(merged_subgraph))
    pop_target = partition["population"][partIDs[0]] 
    subgraph_pop = pop_target + partition["population"][partIDs[1]] 
    components = split_graph_by_pop(merged_subgraph.graph, pop_target, subgraph_pop, epsilon)
    flips = dict.fromkeys(components[0], partIDs[0]) | dict.fromkeys(components[1], partIDs[1]) 
    return partition.flip(flips)


def gen_mmd_configs(n_reps: int) -> list[tuple]:
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


def gen_smd_graph(partition: Partition) -> nx.Graph:
    edgelist = []
    for edge in partition["cut_edges"]:
        edgelist.append((partition.assignment[edge[0]], partition.assignment[edge[1]]))
    return nx.Graph(edgelist)


def cut_smd_graph(graph: nx.Graph, mmd_config: tuple, cut_iterations: int = 100000, node_repeats: int = 20) -> nx.Graph:
    for _ in range(node_repeats):
        spanning_tree: nx.Graph = rand_spanning_tree(graph, list(graph.edges))
        for _ in range(cut_iterations):
            random_edges: list[tuple] = random.sample(list(spanning_tree.edges), sum(mmd_config)-1)
            spanning_tree.remove_edges_from(random_edges)
            sizes = [len(component) for component in nx.connected_components(spanning_tree)]
            if sizes.count(3) == mmd_config[0] and sizes.count(4) == mmd_config[1] and sizes.count(5) == mmd_config[2]:
                return spanning_tree
            spanning_tree.add_edges_from(random_edges)
    raise Exception("partitioning failed after %d random cut iterations after %d node repeats" % (cut_iterations, node_repeats))


def gen_mmd_seed_assignment(smd_partition: Partition) -> dict[int, int]:
    mmd_config = gen_mmd_configs(len(smd_partition.parts))[1]
    print("mmd config = %s" % str(mmd_config))
    smd_graph: nx.Graph = gen_smd_graph(smd_partition)
    smd_forest = cut_smd_graph(smd_graph, mmd_config)
    assignment = {}
    for idx, component in enumerate(nx.connected_components(smd_forest)):
        for partID in component:
            for precID in smd_partition.parts[partID]:
                assignment[precID] = idx+1
    return assignment


def gen_random_map(chain: MarkovChain) -> Partition:
    for partition in chain:
        partition.test_field = 3
        continue
    return partition


def gen_ensemble(chain: MarkovChain, num_maps) -> list[Partition]:
    return [gen_random_map(chain) for _ in range(num_maps)]


# def precinct_ranked_choice(district: Partition, precinctID: int) -> list:
    


# def ranked_choice_election(partition: Partition, voting_function: Callable[[]] = party_line_voting)

# def memoize_markov_chain(markov_chain: MarkovChain):






def main() -> None:
    prs = Presentation()

    prec_graph: gerrychain.Graph = Graph.from_json(GRAPH_FILE)
    prec_geometries: GeoSeries = GeoSeries.from_file(SHAPE_FILE)
    smd_partition: Partition = Partition(prec_graph, assignment=SMD_ASSIGNMENT_COL)

    mmd_partition : Partition = Partition(
        prec_graph, 
        assignment=gen_mmd_seed_assignment(smd_partition),
        updaters={"cut_edges": cut_edges, "population": Tally(POP_COL, "population")} 
    )

    chain = MarkovChain(
        partial(mmd_recom, epsilon=0.01),
        [],
        always_accept,
        mmd_partition,
        total_steps=10
    )

    ensemble: list[Partition] = gen_ensemble(chain, 10)
    for partition in ensemble:
        plot_partition(partition, prec_geometries, prs, show=False)
    prs.save("%s" % PRES_FILE)
    print("done, saved as %s" % PRES_FILE)

    # try:
    #     prev_time = time.process_time_ns()
    #     for stepno, partition in enumerate(chain):
    #         curr_time = time.process_time_ns()
    #         print("chain step total time: %d ms" % (float(curr_time-prev_time)/1000000))
    #         prev_time = curr_time
    #         print("step: %d" % stepno)
    #         print("partition components: %d" % count_components(partition.graph))
    #         # if stepno % PLOT_INTERVAL == 0:
    #         #     plot_partition(partition, prec_geometries, prs, stepno, show=False)
    # except KeyboardInterrupt:
    #     print("keyboard interrupt")
    # finally:
    #     prs.save("%s" % PRES_FILE)
    #     print("done, saved as %s" % PRES_FILE)


if __name__ == "__main__":
    main()