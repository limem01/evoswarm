"""Neo4j-backed memory for EvoSwarm collective with full-text search."""
import asyncio
from datetime import datetime
from typing import Any
from neo4j import AsyncGraphDatabase


class Neo4jMemory:
    """Knowledge graph memory using Neo4j."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Close the database connection."""
        asyncio.create_task(self.driver.close())

    async def setup_indexes(self):
        """Create indexes and full-text search indexes for efficient querying."""
        async with self.driver.session() as session:
            await session.run(
                "CREATE INDEX IF NOT EXISTS FOR (a:Agent) ON (a.name)"
            )
            await session.run(
                "CREATE INDEX IF NOT EXISTS FOR (t:Task) ON (t.id)"
            )
            await session.run(
                "CREATE INDEX IF NOT EXISTS FOR (m:Model) ON (m.version)"
            )
            await session.run(
                "CREATE INDEX IF NOT EXISTS FOR (l:Learning) ON (l.timestamp)"
            )
            # Full-text search indexes
            try:
                await session.run(
                    """
                    CREATE FULLTEXT INDEX learning_search IF NOT EXISTS
                    FOR (l:Learning) ON EACH [l.content, l.category]
                    """
                )
                await session.run(
                    """
                    CREATE FULLTEXT INDEX task_search IF NOT EXISTS
                    FOR (t:Task) ON EACH [t.task, t.result]
                    """
                )
            except Exception:
                # Full-text indexes may already exist or not be supported
                pass

    async def add_agent(self, name: str, role: str, model_version: str = "base"):
        """Add or update an agent in the graph."""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (a:Agent {name: $name})
                SET a.role = $role, a.model_version = $model_version,
                    a.updated_at = datetime()
                """,
                name=name, role=role, model_version=model_version
            )

    async def add_evolution_link(
        self,
        parent_version: str,
        child_version: str,
        metrics: dict[str, Any]
    ):
        """Record an evolution event between model versions."""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (p:Model {version: $parent})
                MERGE (c:Model {version: $child})
                CREATE (p)-[e:EVOLVED_TO {
                    timestamp: datetime(),
                    metrics: $metrics
                }]->(c)
                """,
                parent=parent_version,
                child=child_version,
                metrics=str(metrics)
            )

    async def get_evolution_graph(self) -> dict[str, Any]:
        """Get the full evolution lineage as nodes and links."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (m:Model)
                OPTIONAL MATCH (m)-[e:EVOLVED_TO]->(child:Model)
                RETURN m.version as source,
                       child.version as target,
                       e.metrics as metrics,
                       e.timestamp as timestamp
                """
            )

            nodes = set()
            links = []

            async for record in result:
                source = record["source"]
                target = record["target"]

                nodes.add(source)
                if target:
                    nodes.add(target)
                    links.append({
                        "source": source,
                        "target": target,
                        "metrics": record["metrics"],
                        "timestamp": str(record["timestamp"]) if record["timestamp"] else None,
                    })

            return {
                "nodes": [{"id": n, "label": n} for n in nodes],
                "links": links,
            }

    async def log_task(self, task_id: str, task: str, result: str):
        """Log a completed task."""
        async with self.driver.session() as session:
            await session.run(
                """
                CREATE (t:Task {
                    id: $task_id,
                    task: $task,
                    result: $result,
                    timestamp: datetime()
                })
                """,
                task_id=task_id, task=task, result=result[:5000]
            )

    async def get_recent_tasks(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent tasks."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (t:Task)
                RETURN t.id as id, t.task as task,
                       t.result as result, t.timestamp as timestamp
                ORDER BY t.timestamp DESC
                LIMIT $limit
                """,
                limit=limit
            )

            tasks = []
            async for record in result:
                tasks.append({
                    "id": record["id"],
                    "task": record["task"],
                    "result": record["result"],
                    "timestamp": str(record["timestamp"]) if record["timestamp"] else None,
                })
            return tasks

    async def store_learning(
        self,
        category: str,
        content: str,
        source_task_id: str | None = None
    ):
        """Store a learning from completed tasks."""
        async with self.driver.session() as session:
            query = """
                CREATE (l:Learning {
                    category: $category,
                    content: $content,
                    timestamp: datetime()
                })
            """

            if source_task_id:
                query = """
                    MATCH (t:Task {id: $task_id})
                    CREATE (l:Learning {
                        category: $category,
                        content: $content,
                        timestamp: datetime()
                    })
                    CREATE (t)-[:PRODUCED]->(l)
                """

            await session.run(
                query,
                category=category,
                content=content,
                task_id=source_task_id
            )

    async def get_learnings(
        self,
        category: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Retrieve learnings, optionally filtered by category."""
        async with self.driver.session() as session:
            if category:
                result = await session.run(
                    """
                    MATCH (l:Learning {category: $category})
                    RETURN l.category as category, l.content as content,
                           l.timestamp as timestamp
                    ORDER BY l.timestamp DESC
                    LIMIT $limit
                    """,
                    category=category, limit=limit
                )
            else:
                result = await session.run(
                    """
                    MATCH (l:Learning)
                    RETURN l.category as category, l.content as content,
                           l.timestamp as timestamp
                    ORDER BY l.timestamp DESC
                    LIMIT $limit
                    """,
                    limit=limit
                )

            learnings = []
            async for record in result:
                learnings.append({
                    "category": record["category"],
                    "content": record["content"],
                    "timestamp": str(record["timestamp"]) if record["timestamp"] else None,
                })
            return learnings

    async def search_fulltext(
        self,
        query: str,
        node_type: str = "Learning",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Full-text search across learnings or tasks.

        Args:
            query: Search query string
            node_type: 'Learning' or 'Task'
            limit: Maximum results

        Returns:
            List of matching records with scores
        """
        index_name = "learning_search" if node_type == "Learning" else "task_search"

        async with self.driver.session() as session:
            result = await session.run(
                f"""
                CALL db.index.fulltext.queryNodes($index, $query)
                YIELD node, score
                RETURN node, score
                ORDER BY score DESC
                LIMIT $limit
                """,
                index=index_name,
                query=query,
                limit=limit,
            )

            records = []
            async for record in result:
                node = record["node"]
                entry = dict(node)
                entry["_score"] = record["score"]
                # Convert datetime objects to strings
                for k, v in entry.items():
                    if hasattr(v, "isoformat"):
                        entry[k] = v.isoformat()
                records.append(entry)

            return records
