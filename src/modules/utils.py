from disjoint_set import DisjointSet
import random
import networkx as nx
import decimal
from pathlib import Path
import consts


def rand_spanning_tree(graph: nx.Graph, edges):
    """Modified version of Kruskal's that shuffles an edgelist randomly instead of using a priority queue"""

    spanning_forest: nx.Graph = nx.Graph()
    spanning_forest.add_nodes_from(graph.nodes) 
    random.shuffle(edges)
    ds: DisjointSet = DisjointSet()
    for node in spanning_forest.nodes:
        ds.find(node)
    for u, v in edges:
        if not ds.connected(u, v):
            spanning_forest.add_edge(u, v)
            ds.union(u, v)
    return spanning_forest


def round_up(x: float, place: int=0):
    """Used for more precise rounding up of decimals. Used for rounding the multi-seat election threshold in the ranked-choice tabulation process."""

    context = decimal.getcontext()
    original_rounding = context.rounding
    context.rounding = decimal.ROUND_CEILING

    rounded = round(decimal.Decimal(str(x)), place)
    context.rounding = original_rounding
    return float(rounded)


def round_down(x: float, place: int=0):
    """Used for more precise rounding down of decimals. Used for rounding reweighted ballot weights in the ranked-choice tabulation process."""

    with decimal.localcontext() as ctx:
        d = decimal.Decimal(x)
        ctx.rounding = decimal.ROUND_DOWN
        return float(round(d, place))


def is_path_in_proj(path: Path):
    return consts.PROJ_ROOT in path.parents