"""Pipeline helpers for declarative DAG execution."""

from __future__ import annotations

from collections import deque
from typing import Dict, List

from .parser import PipelineBlock


class PipelineGraph:
    def __init__(self, block: PipelineBlock | None) -> None:
        self.block = block
        self._order: List[str] | None = None

    def is_defined(self) -> bool:
        return self.block is not None

    def topological_order(self) -> List[str]:
        if self.block is None:
            return []
        if self._order is not None:
            return self._order
        indegree: Dict[str, int] = {step.identifier: 0 for step in self.block.steps}
        adjacency: Dict[str, List[str]] = {step.identifier: [] for step in self.block.steps}
        for edge in self.block.edges:
            adjacency[edge.source].append(edge.target)
            indegree[edge.target] += 1
        queue = deque([node for node, deg in indegree.items() if deg == 0])
        order: List[str] = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in adjacency[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
        self._order = order
        return order

    def dependencies_for(self, step_id: str) -> List[str]:
        if self.block is None:
            return []
        deps = []
        for edge in self.block.edges:
            if edge.target == step_id:
                deps.append(edge.source)
        return deps
