import random
from .graph_utils import rand_spanning_tree
from gerrychain import Partition, Graph, MarkovChain 
from gerrychain.accept import always_accept
from functools import partial
import networkx as nx
import logging
from linetimer import CodeTimer
import consts
import run_config
logger = logging.getLogger(__name__)


def mmd_recom(mmd_partition: Partition, mmd_config: dict[int, int], epsilon: float) -> Partition:
    """
    FIX THIS FUNCTION TO WORK GENERICALLY FOR BOTH SMD AND MMD PARTITIONS

    Computes next partition after one step of MMD ReCom. This is a proposal
    function that can be provided to the gerrychain MarkovChain constructor.
    This ReCom algorithm works by merging two adjacent MMD subgraphs, then
    splitting the merged subgraph along a boundary on which each part has a
    population ratio corresponding (within the input epsilon's error) to the
    number of representatives in that district.

    i.e. if a state has 18 representatives, and if districts A and B are
    randomly chosen to be merged and have 3 and 5 representatives respectively,
    re-split them into two parts where district A has 3/18ths of the combined
    population and the district B has 5/18ths of the combined population.

    Each district will retain its designated number of representatives
    throughout all steps of ReCom as specified by mmd_config.

    Arguments:
        partition: an MMD partition
        district_reps: dictionary mapping MMD ID to its assigned number of
        representatives
        epsilon: acceptable population error threshold for split
    Returns:
        a new MMD partition after one step of ReCom
    """

    edge = random.choice(list(mmd_partition[consts.CUT_EDGE_UPDATER]))
    partIDs = (mmd_partition.assignment[edge[0]], mmd_partition.assignment[edge[1]])
    logging.debug("doing recom on districts %d, %d" % (partIDs[0], partIDs[1]))
    merged_subgraph = mmd_partition.graph.subgraph(mmd_partition.parts[partIDs[0]] | mmd_partition.parts[partIDs[1]])
    subgraph_pop = mmd_partition["population"][partIDs[0]] + mmd_partition["population"][partIDs[1]] 
    subgraph_reps = mmd_config[partIDs[0]] + mmd_config[partIDs[1]]
    pop_target = (float(mmd_config[partIDs[0]])/subgraph_reps)*subgraph_pop
    components, complement_or_not = split_graph_by_pop(merged_subgraph.graph, pop_target, subgraph_pop, epsilon)
    if complement_or_not: # component 0 matches the target pop
        flips = dict.fromkeys(components[0], partIDs[0]) | dict.fromkeys(components[1], partIDs[1]) 
    else:
        flips = dict.fromkeys(components[0], partIDs[1]) | dict.fromkeys(components[1], partIDs[0]) 
    return mmd_partition.flip(flips)


def split_graph_by_pop(graph: nx.Graph, pop_target: int, graph_pop: int, epsilon: float, node_repeats: int = 30) -> tuple[tuple[list[int], list[int]], bool]:
    pop_rng = (pop_target * (1 - epsilon), pop_target * (1 + epsilon))
    graph_edges = list(graph.edges)
    for i in range(node_repeats):
        with CodeTimer("create spanning tree", logger_func=logger.debug):
            spanning_tree = rand_spanning_tree(graph, graph_edges)
        root = random.choice(list(spanning_tree.nodes))
        complement_or_not, cut_edge = find_cut(graph, spanning_tree, root, None, graph_pop, pop_rng)
        if cut_edge:
            logging.debug("finished recom after %d random spanning trees on %d nodes" % (i+1, len(spanning_tree.nodes)))
            spanning_tree.remove_edge(cut_edge[0], cut_edge[1])
            comp_1 = [node for node in nx.dfs_postorder_nodes(spanning_tree, source=cut_edge[0])]
            comp_2 = [node for node in nx.dfs_postorder_nodes(spanning_tree, source=cut_edge[1])]
            return((comp_1, comp_2), complement_or_not)
    raise Exception("partitioning failed; could not find cut meeting population constraints")


def find_cut(graph: Graph, tree: Graph, curr_node: int, parent: int, graph_pop: int, pop_rng: tuple) -> tuple:
    sum = graph.nodes[curr_node][consts.POP_COL] 
    for child in tree.neighbors(curr_node):
        if child != parent:
            child_sum, edge_found = find_cut(graph, tree, child, curr_node, graph_pop, pop_rng) 
            if edge_found:
                return (child_sum, edge_found)
            sum += child_sum
    if pop_rng[0] <= sum <= pop_rng[1]:
        return (True, (curr_node, parent))
    elif pop_rng[0] <= graph_pop-sum <= pop_rng[1]:
        return (False, (curr_node, parent))
    return (sum, None)


def gen_random_map(seed_partition: Partition, mmd_config: dict[int, int], n_recom_steps: int, epsilon: float) -> Partition:
    chain = MarkovChain( 
        partial(mmd_recom, mmd_config=mmd_config, epsilon=epsilon),
        [],
        always_accept,
        seed_partition,
        total_steps=n_recom_steps
    )
    for partition in chain:
        continue
    return partition


def gen_ensemble(seed_partition: Partition, mmd_config: dict[int, int], n_maps: int, n_recom_steps: int) -> list[Partition]:
    return [gen_random_map(seed_partition, mmd_config, n_recom_steps) for _ in range(n_maps)]