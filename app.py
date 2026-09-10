"""
app.py

AD Attack Path Mapper - a small blue team tool for visualizing how an
attacker could climb from a low-privilege account to Domain Admin inside
a simulated company network.

There's no real Active Directory domain behind this, the environment
lives in data/ad_environment.json, a fake company with realistic users,
groups, computers, and permission relationships between them. That's
actually how the professional version of this idea works too, tools
like BloodHound collect this same kind of graph data from a real domain
and then answer the exact same question this project answers: "what's
the shortest way from here to full compromise?"
"""

import os

from flask import Flask, render_template, jsonify, request

from graph import load_graph, find_path, compute_stats, graph_to_vis_format

app = Flask(__name__)

GRAPH, RAW_DATA = load_graph()


@app.route("/")
def dashboard():
    stats = compute_stats(GRAPH)
    users = sorted(
        [n for n, d in GRAPH.nodes(data=True) if d.get("type") == "user"],
        key=lambda n: n != "administrator"  # keep administrator visible but not first
    )
    return render_template(
        "dashboard.html",
        company=RAW_DATA["company"],
        stats=stats,
        users=users,
    )


@app.route("/api/graph")
def api_graph():
    return jsonify(graph_to_vis_format(GRAPH))


@app.route("/api/path")
def api_path():
    start = request.args.get("start", "")
    return jsonify(find_path(GRAPH, start))


@app.route("/api/stats")
def api_stats():
    return jsonify(compute_stats(GRAPH))

@app.route("/health")
def health():
    """Simple check to confirm the server is running."""
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)
