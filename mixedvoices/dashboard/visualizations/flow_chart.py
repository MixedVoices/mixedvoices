from collections import defaultdict
from typing import Dict, Set

import networkx as nx
import numpy as np
import plotly.graph_objects as go


class FlowChart:
    def __init__(self, flow_data: Dict, is_recording_flow: bool = False):
        self.flow_data = flow_data
        self.is_recording_flow = is_recording_flow
        self.G = nx.DiGraph()
        self.pos = {}
        self.parent_child = {}
        self.tree_roots = []
        self.node_tree_map = {}  # Maps nodes to their tree index

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
        # Build the graph
        for step in self.flow_data["steps"]:
            self.G.add_node(step["id"], name=step["name"], data=step)
            for next_step_id in step["next_step_ids"]:
                self.G.add_edge(step["id"], next_step_id)
                if next_step_id not in self.parent_child:
                    self.parent_child[next_step_id] = []
                self.parent_child[next_step_id].append(step["id"])

        # Find root nodes (nodes with no parents)
        self.tree_roots = [
            node for node in self.G.nodes() if node not in self.parent_child
        ]

        self._calculate_tree_positions()

    def _get_tree_nodes(self, root: str, visited: Set[str] = None) -> Set[str]:
        """Get all nodes in a tree starting from the given root"""
        if visited is None:
            visited = set()

        if root in visited:
            return visited

        visited.add(root)
        for successor in self.G.successors(root):
            self._get_tree_nodes(successor, visited)

        return visited

    def _calculate_node_levels(self, root: str) -> Dict[str, int]:
        """Calculate levels for nodes in a tree"""
        levels = {root: 0}
        queue = [(root, 0)]
        visited = {root}

        while queue:
            node, level = queue.pop(0)
            for successor in self.G.successors(node):
                if successor not in visited:
                    levels[successor] = level + 1
                    queue.append((successor, level + 1))
                    visited.add(successor)

        return levels

    def _calculate_tree_positions(self) -> None:
        """Calculate positions for nodes treating each root as a separate tree"""
        if not self.tree_roots:
            return

        # First position each tree independently
        for root_idx, root in enumerate(self.tree_roots):
            self._position_single_tree(root, root_idx)

        # Adjust tree spacing and center everything
        self._adjust_tree_spacing()
        self._center_entire_graph()

    def _position_single_tree(self, root: str, tree_idx: int) -> None:
        """Position nodes within a single tree using a modified hierarchical layout"""
        tree_nodes = self._get_tree_nodes(root)
        levels = self._calculate_node_levels(root)

        # Group nodes by level
        nodes_by_level = defaultdict(list)
        for node in tree_nodes:
            level = levels[node]
            nodes_by_level[level].append(node)

        # Calculate x positions level by level
        x_positions = {}
        x_positions[root] = 0  # Start root at 0

        # Process each level
        max_level = max(levels.values())
        for level in range(max_level + 1):
            level_nodes = nodes_by_level[level]

            if level == 0:
                continue  # Root already positioned

            # First pass: position based on parents
            for node in level_nodes:
                parents = [p for p in self.parent_child[node] if p in tree_nodes]
                if parents:
                    parent_positions = [x_positions[p] for p in parents]
                    x_positions[node] = sum(parent_positions) / len(parent_positions)
                else:
                    # Fallback for nodes with no positioned parents
                    x_positions[node] = 0

            # Second pass: ensure spacing
            sorted_nodes = sorted(level_nodes, key=lambda n: x_positions[n])
            min_spacing = 1.0

            # Adjust positions to maintain minimum spacing
            for i in range(1, len(sorted_nodes)):
                curr_node = sorted_nodes[i]
                prev_node = sorted_nodes[i - 1]
                if x_positions[curr_node] - x_positions[prev_node] < min_spacing:
                    x_positions[curr_node] = x_positions[prev_node] + min_spacing

            # Center the level
            if sorted_nodes:
                level_min = x_positions[sorted_nodes[0]]
                level_max = x_positions[sorted_nodes[-1]]
                level_center = (level_min + level_max) / 2
                offset = -level_center  # Center around 0
                for node in sorted_nodes:
                    x_positions[node] += offset

        # Set final positions
        for node in tree_nodes:
            self.pos[node] = (x_positions[node], -levels[node])
            self.node_tree_map[node] = tree_idx

    def _adjust_tree_spacing(self) -> None:
        """Adjust spacing between trees to prevent overlap"""
        if len(self.tree_roots) <= 1:
            return

        # Calculate bounding box for each tree
        tree_bounds = {}
        for node, (x, y) in self.pos.items():
            tree_idx = self.node_tree_map[node]
            if tree_idx not in tree_bounds:
                tree_bounds[tree_idx] = [float("inf"), float("-inf")]
            tree_bounds[tree_idx][0] = min(tree_bounds[tree_idx][0], x)
            tree_bounds[tree_idx][1] = max(tree_bounds[tree_idx][1], x)

        # Adjust positions tree by tree
        tree_spacing = 2
        current_x = 0

        for tree_idx in sorted(tree_bounds.keys()):
            tree_width = tree_bounds[tree_idx][1] - tree_bounds[tree_idx][0]
            tree_center = (tree_bounds[tree_idx][0] + tree_bounds[tree_idx][1]) / 2
            offset = current_x - tree_center

            # Move all nodes in this tree
            for node, (x, y) in list(self.pos.items()):
                if self.node_tree_map[node] == tree_idx:
                    self.pos[node] = (x + offset, y)

            current_x += tree_width + tree_spacing

    def _center_entire_graph(self) -> None:
        """Center the entire graph around (0,0)"""
        if not self.pos:
            return

        # Calculate current bounds
        min_x = min(x for x, y in self.pos.values())
        max_x = max(x for x, y in self.pos.values())

        # Calculate centering offset
        center_x = (min_x + max_x) / 2
        offset_x = -center_x

        # Apply offset to all nodes
        for node in self.pos:
            x, y = self.pos[node]
            self.pos[node] = (x + offset_x, y)

    def _create_edge_trace(self) -> go.Scatter:
        """Create edge trace for visualization with curved edges"""
        edge_x = []
        edge_y = []

        for edge in self.G.edges():
            x0, y0 = self.pos[edge[0]]
            x1, y1 = self.pos[edge[1]]

            # Only curve edges that span multiple levels
            if abs(y1 - y0) > 1:
                # Create curved path using quadratic Bezier curve
                control_x = (x0 + x1) / 2
                control_y = (y0 + y1) / 2

                # Generate points along the curve
                t = np.linspace(0, 1, 20)
                curve_x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * control_x + t**2 * x1
                curve_y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * control_y + t**2 * y1

                edge_x.extend(curve_x.tolist() + [None])
                edge_y.extend(curve_y.tolist() + [None])
            else:
                # Use straight lines for adjacent levels
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
        node_ids = []
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
                failure_rate = (
                    node_data["number_of_failed_calls"]
                    / node_data["number_of_calls"]
                    * 100
                    if node_data["number_of_calls"] > 0
                    else 0
                )
                success_rate = 100 - failure_rate
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
            f"Failed: {node_data['number_of_failed_calls']}<br>"
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
