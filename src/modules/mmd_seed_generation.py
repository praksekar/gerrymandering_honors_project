from gerrychain import Partition
import networkx as nx
import random
from gerrychain.updaters import Tally, cut_edges
from .graph_utils import rand_spanning_tree
import itertools
from linetimer import CodeTimer
from networkx import Graph
flatten = itertools.chain.from_iterable
import consts
import logging
logger = logging.getLogger(__name__)


def gen_mmd_configs(n_reps: int) -> list[dict[int, int]]:
    """
    Generates all possible mappings from MMD IDs to number of representatives in
    that MMD, given a number of representatives in a state. Adheres to the
    requirement in H.R. 3863 that all MMDs have 3 to 5 representatives.

    Arguments:
        n_reps: total number of representatives in the state
    Returns:
        List of MMD config 3-tuples
    """

    configs = []
    for x1 in range(n_reps//3+1):
        for x2 in range(n_reps//4+1):
            for x3 in range(n_reps//5+1):
                if x1*3 + x2*4 + x3*5 == n_reps:
                    configs.append(dict.fromkeys(range(1, x1+1), 3) 
                        | dict.fromkeys(range(x1+1, x1+x2+1), 4) 
                        | dict.fromkeys(range(x1+x2+1, x1+x2+x3+1), 5))
    return configs


def gen_smd_adjacency_graph(smd_partition: Partition) -> nx.Graph:
    """
    Constructs an SMD adjacency graph based on the input SMD partition.

    Arguments:
        partition: gerrychain Partition initialized with an SMD assignment
    Returns:
        adjacency graph of SMDs
    """

    edgelist = []
    for edge in smd_partition["cut_edges"]:
        edgelist.append((smd_partition.assignment[edge[0]], smd_partition.assignment[edge[1]]))
    return nx.Graph(edgelist)


def cut_smd_adjacency_graph(graph: nx.Graph, mmd_config: dict[int, int], cut_iterations: int = 100000, node_repeats: int = 20) -> nx.Graph:
    """
    Attempts to partition input SMD adjacency graph into connected subgraphs
    with sizes that correspondingly match with each district's number of
    representatives specified by the MMD config. 
    
    Generates random spanning tree of SMD graph and randomly cuts away the
    number of desired districts in the MMD - 1 edges from the graph. If the
    number of nodes in each of the cut spanning tree's subgraphs match the
    proportions of the MMD config, it is returned.

    Arguments:
        graph: SMD adjacency graph
        mmd_config: MMD config
        cut_iterations: max number of cut attempts for each randomly generated
        spanning tree
        node_repeats: max number of spanning trees to build
    Returns:
        networkx Graph spanning tree forest that matches input MMD config's
        proportions
    """

    config_sizes = sorted(list(mmd_config.values()))
    for _ in range(node_repeats):
        spanning_tree: nx.Graph = rand_spanning_tree(graph, list(graph.edges))
        edges = list(spanning_tree.edges)
        for _ in range(cut_iterations):
            random_edges: list[tuple] = random.sample(edges, len(mmd_config)-1)
            spanning_tree.remove_edges_from(random_edges)
            forest_sizes = [len(component) for component in nx.connected_components(spanning_tree)]
            if sorted(forest_sizes) == config_sizes:
                return spanning_tree
            spanning_tree.add_edges_from(random_edges)
    raise Exception("partitioning failed after %d random cut iterations after %d node repeats" % (cut_iterations, node_repeats))


def gen_mmd_seed_assignment(smd_partition: Partition, mmd_config: dict[int, int]) -> dict[int, int]:
    """
    Generates initial MMD assignment dict that maps precinct IDs to district
    IDs. This will be used as the assignment parameter to the gerrychain
    Partition constructor.

    Algorithm first generates an SMD adjacency graph, cuts it into the desired
    MMD representative proportions specified by mmd_config, and then generates
    and returns the precinct assignment dict.

    Arguments:
        partition: gerrychain Partition initialized with an SMD assignment
    Returns:
        assignment dictionary mapping precinct IDs to district IDs
    """

    smd_graph: nx.Graph = gen_smd_adjacency_graph(smd_partition)
    with CodeTimer("cutting smd graph into proportions specified by config"):
        smd_forest = cut_smd_adjacency_graph(smd_graph, mmd_config)
    components = [c for c in nx.connected_components(smd_forest)]
    prec_assignment = {}
    for districtID, n_reps in mmd_config.items():
        for component in components:
            if len(component) == n_reps:
                component_precIDs = flatten([smd_partition.parts[n] for n in component])
                prec_assignment = prec_assignment | dict.fromkeys(component_precIDs, districtID)
                components.remove(component)
                break
    return prec_assignment


def gen_mmd_seed_partition(smd_partition: Partition, mmd_config: dict[int, int]) -> Partition:
    logger.info("Using MMD config: %s" % str(mmd_config))
    mmd_assignment: dict[int, int] = gen_mmd_seed_assignment(smd_partition, mmd_config)
    return Partition(
        graph=smd_partition.graph, 
        assignment=mmd_assignment,
        updaters={consts.CUT_EDGE_UPDATER: cut_edges, consts.POP_UPDATER: Tally(consts.POP_COL, consts.POP_UPDATER)}
    )