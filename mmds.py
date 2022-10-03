import random
from functools import partial
import gerrychain
import matplotlib.pyplot as plt
import networkx as nx
from geopandas import GeoSeries
from gerrychain import Graph, MarkovChain, Partition, constraints
from gerrychain.accept import always_accept
from gerrychain.tree import random_spanning_tree
from gerrychain.updaters import Tally, cut_edges
from matplotlib.colors import ListedColormap
from pptx import Presentation


SHAPE_FILE = "./state_data/PA/PA.shp"
GRAPH_FILE = "./PAjson_wo_geometry"
PRES_FILE = "./pres_output/mmd_recom2"
SMD_ASSIGNMENT_COL = "CD_2011"
MARKOV_CHAIN_STEPS = 500
POP_COL = "TOTPOP"
COLORS = ListedColormap(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
'#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff',
'#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075',
'#808080'])


def add_plot_to_pres(prs):
    plt.savefig("/tmp/graph.png")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture("/tmp/graph.png", 0, 0)
    print("slide added")


def plot_partition(partition: Partition, precinct_geometries: GeoSeries, prs, show=False, cmap=COLORS):
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
    components = [c for c in nx.connected_components(G)]
    return len(components)


def tree_pop(tree, root):
    pop = 0
    for nodeID in nx.dfs_postorder_nodes(tree, source=root):
        pop += tree.nodes[nodeID][POP_COL]
    return pop


def split_graph_by_pop(graph: nx.Graph, pop_target: int, graph_pop: int, epsilon: float, node_repeats: int = 10) -> tuple[list[int]]:
    pop_rng = (pop_target * (1 - epsilon), pop_target * (1 + epsilon))
    for i in range(node_repeats):
        spanning_tree = random_spanning_tree(graph)
        edges_left = set(spanning_tree.edges)
        for j in range(len(edges_left)):
            rand_edge = random.choice(list(edges_left))
            spanning_tree.remove_edge(rand_edge[0], rand_edge[1])
            comp_pop = tree_pop(spanning_tree, rand_edge[0])
            if pop_rng[0] <= comp_pop <= pop_rng[1] or pop_rng[0] <= graph_pop-comp_pop <= pop_rng[1]:
                print("finished recom after %d iterations" % ((i+1)*(j+1)))
                return([node for node in nx.dfs_postorder_nodes(spanning_tree, source=rand_edge[0])],
                       [node for node in nx.dfs_postorder_nodes(spanning_tree, source=rand_edge[1])])
            spanning_tree.add_edge(rand_edge[0], rand_edge[1])
            edges_left.remove(rand_edge)
    raise Exception("partitioning failed after %d random cut iterations after %d node repeats" % (len(edges_left), node_repeats))


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
        spanning_tree: nx.Graph = nx.random_spanning_tree(graph)
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
        partial(mmd_recom, epsilon=0.1),
        [],
        always_accept,
        mmd_partition,
        MARKOV_CHAIN_STEPS
    )

    try:
        for stepno, partition in enumerate(chain):
            print("step: %d" % stepno)
            print("partition components: %d" % count_components(partition.graph))
            plot_partition(partition, prec_geometries, prs=prs, show=False)
    except KeyboardInterrupt:
        print("keyboard interrupt")
    finally:
        prs.save("%s" % PRES_FILE)
        print("done, saved as %s" % PRES_FILE)


if __name__ == "__main__":
    main()