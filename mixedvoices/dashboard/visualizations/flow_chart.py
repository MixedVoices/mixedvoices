from typing import Dict, List

import networkx as nx
import plotly.graph_objects as go


class FlowChart:
    def __init__(self, flow_data: Dict, is_recording_flow: bool = False):
        self.flow_data = flow_data
        self.is_recording_flow = is_recording_flow
        self.G = nx.DiGraph()
        self.pos = {}
        self.parent_child = {}

    def _create_graph(self) -> None:
        """Create networkx graph from flow data"""
        if self.is_recording_flow:
            self._create_recording_graph()
        else:
            self._create_full_graph()

    def _create_recording_graph(self) -> None:
        """Create a simple linear graph for recording flow"""
        steps = self.flow_data.get("steps", [])
        if not steps:
            return

        for i, step in enumerate(steps):
            self.G.add_node(step["id"], name=step["name"], data=step)
            if i > 0:
                self.G.add_edge(steps[i - 1]["id"], step["id"])

        # Create vertical layout
        step_count = len(steps)
        total_height = step_count - 1
        for i, step in enumerate(steps):
            y = -(i - (total_height / 2))
            self.pos[step["id"]] = (0, y)

    def _create_full_graph(self) -> None:
        """Create graph for full flow visualization"""
        for step in self.flow_data["steps"]:
            self.G.add_node(step["id"], name=step["name"], data=step)
            for next_step_id in step["next_step_ids"]:
                self.G.add_edge(step["id"], next_step_id)
                if next_step_id not in self.parent_child:
                    self.parent_child[next_step_id] = []
                self.parent_child[next_step_id].append(step["id"])

        self._calculate_positions()

    def _calculate_positions(self) -> None:
        """Calculate node positions for visualization"""
        # Find root nodes and calculate levels
        root_nodes = [node for node in self.G.nodes() if node not in self.parent_child]
        levels = self._calculate_levels(root_nodes)

        # Position nodes by level
        self._position_nodes_by_level(levels)

    def _calculate_levels(self, root_nodes: List) -> Dict:
        """Calculate node levels using BFS"""
        levels = {node: -1 for node in self.G.nodes()}
        current_level = 0
        current_nodes = root_nodes

        while current_nodes:
            next_nodes = []
            for node in current_nodes:
                if levels[node] == -1:
                    levels[node] = current_level
                    next_nodes.extend(list(self.G.successors(node)))
            current_nodes = next_nodes
            current_level += 1

        return levels

    def _position_nodes_by_level(self, levels: Dict) -> None:
        """Position nodes based on their levels"""
        max_level = max(levels.values())
        nodes_by_level = {}

        # Group nodes by level
        for node, level in levels.items():
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)

        # Position nodes level by level
        for level in range(max_level + 1):
            nodes = nodes_by_level.get(level, [])
            if len(nodes) == 1:
                node = nodes[0]
                parent_nodes = self.parent_child.get(node, [])
                if parent_nodes and parent_nodes[0] in self.pos:
                    self.pos[node] = (self.pos[parent_nodes[0]][0], -level)
                else:
                    self.pos[node] = (0, -level)
            else:
                total_width = len(nodes) - 1
                for i, node in enumerate(sorted(nodes)):
                    x = i - total_width / 2
                    self.pos[node] = (x, -level)

    def _create_edge_trace(self) -> go.Scatter:
        """Create edge trace for visualization"""
        edge_x = []
        edge_y = []

        for edge in self.G.edges():
            x0, y0 = self.pos[edge[0]]
            x1, y1 = self.pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        return go.Scatter(
            x=edge_x,
            y=edge_y,
            line={"width": 1, "color": "#888"},
            hoverinfo="none",
            mode="lines",
            showlegend=False,
        )

    def _create_node_trace(self) -> go.Scatter:
        """Create node trace for visualization"""
        node_x = []
        node_y = []
        node_text = []
        node_hover = []
        node_colors = []
        node_ids = []  # For customdata

        for node in self.G.nodes():
            x, y = self.pos[node]
            node_x.append(x)
            node_y.append(y)

            node_data = self.G.nodes[node]["data"]
            node_ids.append(node_data["id"])

            if self.is_recording_flow:
                color = "#4B89DC"
                hover = f"Step: {node_data['name']}"
            else:
                success_rate = (
                    node_data["number_of_successful_calls"]
                    / node_data["number_of_calls"]
                    * 100
                    if node_data["number_of_calls"] > 0
                    else 0
                )
                color = self._get_color_by_success_rate(success_rate)
                hover = self._create_hover_text(node_data, success_rate)

            node_colors.append(color)
            node_text.append(node_data["name"])
            node_hover.append(hover)

        return go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            name="",
            hoverinfo="text",
            text=node_text,
            textposition="bottom center",
            hovertext=node_hover,
            customdata=node_ids,
            marker={
                "showscale": False,
                "size": 30,
                "color": node_colors,
                "line": {"width": 2, "color": "white"},
            },
        )

    @staticmethod
    def _get_color_by_success_rate(success_rate: float) -> str:
        if success_rate >= 80:
            return "#198754"  # Success green
        elif success_rate >= 60:
            return "#fd7e14"  # Warning orange
        return "#dc3545"  # Danger red

    @staticmethod
    def _create_hover_text(node_data: Dict, success_rate: float) -> str:
        return (
            f"Step: {node_data['name']}<br>"
            f"Total Calls: {node_data['number_of_calls']}<br>"
            f"Successful: {node_data['number_of_successful_calls']}<br>"
            f"Success Rate: {success_rate:.1f}%"
        )

    def create_figure(self) -> go.Figure:
        """Create and return the plotly figure"""
        self._create_graph()

        # Create edge trace
        edge_trace = self._create_edge_trace()

        # Create node trace
        node_trace = self._create_node_trace()

        return go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                showlegend=False,
                hovermode="closest",
                margin={"b": 20, "l": 5, "r": 5, "t": 40},
                xaxis={
                    "showgrid": False,
                    "zeroline": False,
                    "showticklabels": False,
                },
                yaxis={
                    "showgrid": False,
                    "zeroline": False,
                    "showticklabels": False,
                },
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                clickmode="event",
                height=600,
                dragmode=False,
            ),
        )
