import logging
import sys
from datetime import datetime
from typing import List, Tuple

from neo4j import GraphDatabase, Query

from ride.events.transit_completed import TransitCompleted
from fastapi_events.handlers.local import local_handler
from fastapi_events.typing import Event


class GraphTransitAnalyzer:
    graph_db: GraphDatabase

    def __init__(self):
        self.graph_db = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        logging.getLogger("neo4j").addHandler(handler)
        logging.getLogger("neo4j").setLevel(logging.INFO)

    @staticmethod
    def _analyze(tx, client_id: int, address_hash: int):
        query = (
            f"MATCH p=(a:Address)-[:Transit*]->(:Address) "
            f"WHERE a.hash = {address_hash} "
            f"AND (ALL(x IN range(1, length(p)-1) WHERE ((relationships(p)[x]).clientId = {client_id}) AND "
            f"0 <= duration.inSeconds( "
            f"(relationships(p)[x-1]).completeAt, (relationships(p)[x]).started).minutes <= 15)"
            f") "
            f"AND length(p) >= 1 "
            f"RETURN [x in nodes(p) | x.hash] AS hashes ORDER BY length(p) DESC LIMIT 1"
        )
        result = tx.run(query)
        return [row["hashes"] for row in result]

    def analyze(self, client_id: int, address_hash: int) -> List[int]:
        with self.graph_db.session() as session:
            result = session.read_transaction(self._analyze, client_id, address_hash)
        self.on_close()
        return result[0] if result else []

    def add_transit_between_addresses(
        self,
        client_id: int,
        transit_id: int,
        address_from_hash: int,
        address_to_hash: int,
        started: datetime,
        complete_at: datetime
    ):
        with self.graph_db.session() as session:
            session.run(Query(f"MERGE (from:Address {{hash: {address_from_hash}}})"))
            session.run(Query(f"MERGE (to:Address {{hash: {address_to_hash}}})"))
            session.run(Query((
                f"MATCH (from:Address {{hash: {address_from_hash}}}), (to:Address {{hash: {address_to_hash}}}) "
                f"CREATE (from)-[:Transit {{clientId: {client_id}, transitId: {transit_id}, "
                f"started: datetime(\"{started.isoformat()}\"),"
                f" completeAt: datetime(\"{complete_at.isoformat()}\") }}]->(to)")))

    def handle(self, event: Tuple[str, TransitCompleted]):
        event_name: str = event[0]
        transit_completed: TransitCompleted = event[1]
        self.add_transit_between_addresses(
            transit_completed.client_id,
            transit_completed.transit_id,
            transit_completed.address_from_hash,
            transit_completed.address_to_hash,
            transit_completed.started,
            transit_completed.complete_at
        )

    def on_close(self):
        if self.graph_db is not None:
            self.graph_db.close()


@local_handler.register(event_name="add_transit_between_addresses")
def handle_add_transit_between_addresses(event: Event):
    graph_transit_analyzer = GraphTransitAnalyzer()
    graph_transit_analyzer.handle(event)
    graph_transit_analyzer.on_close()
