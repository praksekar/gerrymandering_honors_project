from disjoint_set import DisjointSet
import random
import networkx as nx


def rand_spanning_tree(graph: nx.Graph, edges):
    spanning_forest: nx.Graph = nx.Graph() # can we remove next line by putting graph.nodes into this constructor?
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