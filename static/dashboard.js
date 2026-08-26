// dashboard.js
// Renders the AD environment as an interactive graph (vis-network), then
// calls the Flask API to find and highlight the shortest path from a
// chosen account to Domain Admins.

let network = null;
let nodesDS = null;
let edgesDS = null;
let originalNodeStyle = {};   // id -> { background, border } so highlights can be undone cleanly
let currentPathNodeIds = [];
let currentPathEdgeIds = [];

const GROUP_COLORS = {
    user: "#5b8ba0",
    group: "#e0a458",
    computer: "#c17b6d",
};

async function loadGraph() {
    const data = await fetch("/api/graph").then(r => r.json());

    const nodes = data.nodes.map(n => {
        const background = n.highValue ? "#e2483d" : (GROUP_COLORS[n.group] || "#5b8ba0");
        const border = n.highValue ? "#ff8a80" : "rgba(216, 225, 232, 0.3)";
        originalNodeStyle[n.id] = { background, border };

        return {
            id: n.id,
            label: n.label,
            shape: n.group === "computer" ? "box" : (n.group === "group" ? "diamond" : "dot"),
            color: { background, border },
            font: { color: "#0d1b2a", face: "IBM Plex Mono", size: 12 },
            size: n.highValue ? 24 : 16,
            borderWidth: n.highValue ? 3 : 1.5,
        };
    });

    const edges = data.edges.map(e => ({
        id: e.id,
        from: e.from,
        to: e.to,
        label: e.label,
        arrows: "to",
        color: { color: "rgba(216, 225, 232, 0.25)" },
        font: { color: "#8296a8", size: 9, strokeWidth: 0, align: "top" },
        smooth: { type: "cubicBezier", forceDirection: "vertical", roundness: 0.45 },
        width: 1,
    }));

    nodesDS = new vis.DataSet(nodes);
    edgesDS = new vis.DataSet(edges);

    network = new vis.Network(
        document.getElementById("networkGraph"),
        { nodes: nodesDS, edges: edgesDS },
        {
            layout: {
                hierarchical: {
                    direction: "UD",
                    sortMethod: "directed",
                    levelSeparation: 95,
                    nodeSpacing: 105,
                },
            },
            physics: false,
            interaction: { hover: true, zoomView: true, dragView: true },
        }
    );
}

function resetHighlight() {
    if (currentPathNodeIds.length) {
        const resets = currentPathNodeIds.map(id => ({
            id,
            borderWidth: id === "Domain Admins" || id === "administrator" ? 3 : 1.5,
            color: originalNodeStyle[id],
        }));
        nodesDS.update(resets);
    }
    if (currentPathEdgeIds.length) {
        const resets = currentPathEdgeIds.map(id => ({
            id, width: 1, color: { color: "rgba(216, 225, 232, 0.25)" },
        }));
        edgesDS.update(resets);
    }
    currentPathNodeIds = [];
    currentPathEdgeIds = [];
}

function highlightPath(nodeIds) {
    currentPathNodeIds = nodeIds;
    nodesDS.update(nodeIds.map(id => ({
        id,
        borderWidth: 4,
        color: { background: originalNodeStyle[id].background, border: "#e2483d" },
    })));

    for (let i = 0; i < nodeIds.length - 1; i++) {
        currentPathEdgeIds.push(`${nodeIds[i]}__${nodeIds[i + 1]}`);
    }
    edgesDS.update(currentPathEdgeIds.map(id => ({ id, color: { color: "#e2483d" }, width: 3 })));

    network.fit({ nodes: nodeIds, animation: { duration: 600, easingFunction: "easeInOutQuad" } });
}

async function findPath() {
    const start = document.getElementById("startSelect").value;
    const resultArea = document.getElementById("resultArea");
    resultArea.innerHTML = '<p class="result-empty">Searching...</p>';
    resetHighlight();

    const result = await fetch(`/api/path?start=${encodeURIComponent(start)}`).then(r => r.json());

    if (!result.path_found) {
        resultArea.innerHTML = `
            <div class="result-safe">
                <i class="fas fa-shield-halved"></i>${result.message}
            </div>
        `;
        return;
    }

    highlightPath(result.nodes);

    const stepsHtml = result.steps
        .map(s => `<li><span class="step-tag">${s.type}</span>${s.sentence}</li>`)
        .join("");

    const fixesHtml = result.recommendations
        .map(f => `<li><i class="fas fa-check"></i>${f}</li>`)
        .join("");

    resultArea.innerHTML = `
        <div class="result-header">
            <h3>Path Found</h3>
            <span class="hops">${result.hop_count} hops</span>
        </div>
        <ul class="step-list">${stepsHtml}</ul>
        ${fixesHtml ? `
            <div class="recommendations">
                <h4><i class="fas fa-wrench"></i> What to fix</h4>
                <ul class="fix-list">${fixesHtml}</ul>
            </div>
        ` : ""}
    `;
}

loadGraph();
