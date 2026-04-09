"""NetworkX-based collusion ring detection."""

from uuid import UUID

import networkx as nx
from sqlalchemy.orm import Session

from ..repositories.vector_repo import VectorRepository


class GraphService:
    def __init__(self, db: Session):
        self.vector_repo = VectorRepository(db)

    def find_collusion_groups(self, task_id: UUID) -> dict:
        """
        Build a graph from student pairs with pairwise similarity > 30%.
        Return connected components (collusion clusters).
        """
        pairs = self.vector_repo.get_collusion_pairs(task_id)

        if not pairs:
            return {"total_groups": 0, "groups": []}

        G = nx.Graph()
        for name1, name2 in pairs:
            G.add_edge(name1, name2)

        clusters = [sorted(c) for c in nx.connected_components(G)]
        return {"total_groups": len(clusters), "groups": clusters}
