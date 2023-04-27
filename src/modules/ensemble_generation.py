import random
from .utils import rand_spanning_tree
from itertools import product
from gerrychain import Partition, Graph, MarkovChain 
from gerrychain.accept import always_accept
from functools import partial
from ..custom_types import VMDPartition, Ensemble
import networkx as nx
import logging
from linetimer import CodeTimer
import consts
logger = logging.getLogger(__name__)
import multiprocessing
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool


def vmd_recom(partition: VMDPartition, epsilon: float) -> Partition:
    """
    Modified version of ReCom that works additionally with MMDs. This is a
    "proposal" function that can be provided to the gerrychain MarkovChain
    constructor.  This ReCom algorithm works by merging two adjacent district
    subgraphs, then splitting the merged subgraph along a boundary on which each
    part has a population ratio corresponding (within the input epsilon's error)
    to the number of representatives in that district.

    i.e. if a state has 18 representatives, and if districts A and B are
    randomly chosen to be merged and have 3 and 5 representatives respectively,
    re-split them into two parts where district A has 3/18ths of the combined
    population and the district B has 5/18ths of the combined population. In the
    SMD case, the new split will effectively divide subgraph into districts of
    equal population.

    Each district will retain its designated number of representatives
    throughout all steps of ReCom as specified by the district_reps field of the
    VMDPartition.


    Arguments:
        partition: a VMD partition
        epsilon: acceptable population error threshold for split
    Returns:
        a new MMD partition after one step of ReCom
    """

    edge = random.choice(list(partition[consts.CUT_EDGE_UPDATER]))
    partIDs = (partition.assignment[edge[0]], partition.assignment[edge[1]])
    logger.debug("doing recom on districts %d, %d" % (partIDs[0], partIDs[1]))
    merged_subgraph = partition.graph.subgraph(partition.parts[partIDs[0]] | partition.parts[partIDs[1]])
    subgraph_pop = partition["population"][partIDs[0]] + partition["population"][partIDs[1]] 
    subgraph_reps = partition.district_reps[partIDs[0]] + partition.district_reps[partIDs[1]]
    pop_target = (float(partition.district_reps[partIDs[0]])/subgraph_reps)*subgraph_pop
    components, complement_or_not = split_graph_by_pop(merged_subgraph.graph, pop_target, subgraph_pop, epsilon)
    if complement_or_not: # component 0 matches the target pop
        flips = dict.fromkeys(components[0], partIDs[0]) | dict.fromkeys(components[1], partIDs[1]) 
    else:
        flips = dict.fromkeys(components[0], partIDs[1]) | dict.fromkeys(components[1], partIDs[0]) 
    return partition.flip(flips)


def split_graph_by_pop(graph: nx.Graph, pop_target: int, graph_pop: int, epsilon: float, node_repeats: int = 500) -> tuple[tuple[list[int], list[int]], bool]:
    pop_rng = (pop_target * (1 - epsilon), pop_target * (1 + epsilon))
    graph_edges = list(graph.edges)
    for i in range(node_repeats):
        spanning_tree = rand_spanning_tree(graph, graph_edges)
        root = random.choice(list(spanning_tree.nodes))
        complement_or_not, cut_edge = find_cut(graph, spanning_tree, root, None, graph_pop, pop_rng)
        if cut_edge:
            logger.debug("finished recom after %d random spanning trees on %d nodes" % (i+1, len(spanning_tree.nodes)))
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


def gen_random_map(seed_partition: VMDPartition, n_recom_steps: int, epsilon: float, constraints: list[str]) -> VMDPartition:
    chain = MarkovChain( 
        partial(vmd_recom, epsilon=epsilon),
        constraints,
        always_accept,
        seed_partition,
        total_steps=n_recom_steps
    )
    for partition in chain:
        continue
    return partition
    

def gen_ensemble(seed_partition: VMDPartition, ensemble_size: int, n_recom_steps: int, epsilon: float, seed_type: str, constraints: list[str]) -> Ensemble:
    logger.info(f"generating ensemble of size {ensemble_size}")
    maps: list[VMDPartition] = [gen_random_map(seed_partition, n_recom_steps, epsilon, constraints) for _ in range(ensemble_size)]
    return Ensemble(maps, n_recom_steps, epsilon, seed_type, constraints)


def gen_random_map_json_dict(seed_partition: dict, n_recom_steps: int, epsilon: float, constraints: list[str]) -> dict:
    seed_partition = VMDPartition.from_json_dict(seed_partition)
    chain = MarkovChain( 
        partial(vmd_recom, epsilon=epsilon),
        constraints,
        always_accept,
        seed_partition,
        total_steps=n_recom_steps
    )
    for i in range(10):
        try:
            for partition in chain:
                continue
            return partition.to_json_dict()
        except:
            logger.warning(f"generating random map failed; retrying")
    raise Exception("generating random map failed after many attempts")


def gen_ensemble_parallel(seed_partition: VMDPartition, ensemble_size: int, n_recom_steps: int, epsilon: float, seed_type: str, constraints: list[str], n_workers: int) -> Ensemble:
    logger.info(f"generating ensemble of size {ensemble_size} in parallel with {n_workers} workers")
    args = (seed_partition.to_json_dict(), n_recom_steps, epsilon, constraints)
    with Pool(n_workers) as p:
        json_maps = p.starmap(gen_random_map_json_dict, [args for _ in range(ensemble_size)])
    with CodeTimer("converting json_maps to VMDPartitions", logger_func=logger.debug):
        p = ThreadPool(n_workers)
        maps = p.map(VMDPartition.from_json_dict, json_maps)
        # maps = [VMDPartition.from_json_dict(json_map) for json_map in json_maps]
    return Ensemble(maps, n_recom_steps, epsilon, seed_type, constraints)







