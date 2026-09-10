"""
graph.py

Loads the simulated AD environment and answers the two questions the
dashboard actually cares about:
  1. Is there a path from this account to Domain Admins?
  2. If so, what is it, in plain English, and what should a blue team fix?

Built on networkx, which already implements solid, well-tested pathfinding
algorithms - no reason to hand-roll BFS for something like this.
"""

import json
import networkx as nx

DATA_PATH = "data/ad_environment.json"
TARGET_NODE = "Domain Admins"

# how to turn one graph edge into a sentence a human can actually read
EDGE_NARRATIVE = {
    "MemberOf": "{u} is a member of {v}",
    "AdminTo": "{u} has local admin rights on {v}",
    "GenericAll": "{u} has full control (GenericAll) over {v}, enough to fully take it over",
    "GenericWrite": "{u} can modify {v}'s account settings (GenericWrite)",
    "ForceChangePassword": "{u} can reset {v}'s password without knowing the original",
    "HasSession": "{v} has an active login session on {u}, exposing their credentials to anyone who compromises this machine",
}

# what a blue team should actually do about each relationship type - shown
# only for the ones that represent a real abusable permission, plain group
# membership isn't something you "fix", it's just structure
EDGE_FIXES = {
    "AdminTo": "Review why this admin relationship exists and scope it down if it isn't needed.",
    "GenericAll": "Remove this permission grant. GenericAll should never sit on a low-privilege group.",
    "GenericWrite": "Restrict this write permission to only what's actually needed.",
    "ForceChangePassword": "Revoke this delegation unless there's a documented reason for it.",
    "HasSession": "Avoid privileged accounts logging into lower-trust machines. Use a dedicated admin workstation instead.",
}


def load_graph():
    """Reads the AD environment JSON and builds a directed graph from it.

    Returns both the networkx graph and the raw parsed data, since a few
    places (like the dashboard) need the original node details too.
    """
    with open(DATA_PATH) as f:
        data = json.load(f)

    G = nx.DiGraph()
    for node in data["nodes"]:
        G.add_node(node["id"], **node)
    for edge in data["edges"]:
        G.add_edge(edge["source"], edge["target"], type=edge["type"])

    return G, data


def find_path(G, start):
    """
    Shortest path from `start` to Domain Admins, if one exists. Returns a
    dict shaped so the API can hand it straight to the frontend.
    """
    if start not in G:
        return {
            "path_found": False,
            "message": f"Account '{start}' wasn't found in this AD environment. Pick one from the dropdown.",
        }

    try:
        path_nodes = nx.shortest_path(G, source=start, target=TARGET_NODE)
    except nx.NetworkXNoPath:
        return {
            "path_found": False,
            "message": f"No path to Domain Admins found from {start}. This account looks safely contained.",
        }

    steps = []
    fixes = []
    for u, v in zip(path_nodes, path_nodes[1:]):
        edge_type = G.edges[u, v]["type"]
        sentence = EDGE_NARRATIVE.get(edge_type, "{u} connects to {v}").format(u=u, v=v)
        steps.append({"source": u, "target": v, "type": edge_type, "sentence": sentence})
        fix = EDGE_FIXES.get(edge_type)
        if fix and fix not in fixes:
            fixes.append(fix)

    return {
        "path_found": True,
        "start": start,
        "target": TARGET_NODE,
        "hop_count": len(path_nodes) - 1,
        "nodes": path_nodes,
        "steps": steps,
        "recommendations": fixes,
    }


def compute_stats(G):
    """
    Domain-wide summary: how many accounts in this environment actually
    have a path to full compromise, not just the one currently selected.
    """
    users = [n for n, d in G.nodes(data=True) if d.get("type") == "user" and n != "administrator"]
    at_risk = 0
    for u in users:
        try:
            nx.shortest_path(G, source=u, target=TARGET_NODE)
            at_risk += 1
        except nx.NetworkXNoPath:
            pass

    return {
        "total_users": sum(1 for _, d in G.nodes(data=True) if d.get("type") == "user"),
        "total_groups": sum(1 for _, d in G.nodes(data=True) if d.get("type") == "group"),
        "total_computers": sum(1 for _, d in G.nodes(data=True) if d.get("type") == "computer"),
        "total_edges": G.number_of_edges(),
        "accounts_checked": len(users),
        "accounts_at_risk": at_risk,
    }


def graph_to_vis_format(G):
    """Converts the networkx graph into the node/edge shape vis-network expects."""
    nodes = []
    for n, d in G.nodes(data=True):
        nodes.append({
            "id": n,
            "label": d.get("label", n),
            "group": d.get("type", "user"),
            "highValue": bool(d.get("high_value", False)),
        })
    edges = []
    for u, v, d in G.edges(data=True):
        edges.append({"from": u, "to": v, "label": d.get("type", ""), "id": f"{u}__{v}"})
    return {"nodes": nodes, "edges": edges}
