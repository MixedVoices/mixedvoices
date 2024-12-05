import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Literal, Optional

PromptType = Literal["project", "version"]


class DatabaseError(Exception):
    """Custom exception for database operations"""

    pass


class DatabaseManager:
    def __init__(self, db_path: str):
        """Initialize DatabaseManager with database path"""
        self.db_path = db_path
        self._setup_logging()
        self._init_database()

    def _setup_logging(self):
        """Setup logging for database operations"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _init_database(self):
        """Initialize the database if it doesn't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Initializing database at {self.db_path}")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Enable foreign key support
            cursor.execute("PRAGMA foreign_keys = ON")

            # Create all tables
            tables = [
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS versions (
                    project_id TEXT,
                    version_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (project_id, version_id),
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS project_paths (
                    id INTEGER PRIMARY KEY,
                    project_id TEXT,
                    path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id),
                    UNIQUE(project_id, path)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS version_paths (
                    id INTEGER PRIMARY KEY,
                    project_id TEXT,
                    version_id TEXT,
                    path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id, version_id) REFERENCES versions(project_id, version_id),
                    UNIQUE(project_id, version_id, path)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS project_failure_reasons (
                    id INTEGER PRIMARY KEY,
                    project_id TEXT,
                    failure_reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id),
                    UNIQUE(project_id, failure_reason)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS version_failure_reasons (
                    id INTEGER PRIMARY KEY,
                    project_id TEXT,
                    version_id TEXT,
                    failure_reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id, version_id) REFERENCES versions(project_id, version_id),
                    UNIQUE(project_id, version_id, failure_reason)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS prompts (
                    prompt_id INTEGER PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    version_id TEXT,
                    prompt_text TEXT NOT NULL,
                    prompt_type TEXT NOT NULL CHECK (prompt_type IN ('project', 'version')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id),
                    FOREIGN KEY (project_id, version_id) REFERENCES versions(project_id, version_id),
                    CHECK ((prompt_type = 'project' AND version_id IS NULL) OR 
                          (prompt_type = 'version' AND version_id IS NOT NULL))
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS evaluations (
                    eval_id INTEGER PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    version_id TEXT,
                    eval_type TEXT NOT NULL CHECK (eval_type IN ('project', 'version')),
                    metrics_dict JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id),
                    FOREIGN KEY (project_id, version_id) REFERENCES versions(project_id, version_id),
                    CHECK ((eval_type = 'project' AND version_id IS NULL) OR 
                        (eval_type = 'version' AND version_id IS NOT NULL))
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS prompt_runs (
                    run_id INTEGER PRIMARY KEY,
                    eval_id INTEGER,
                    prompt_id INTEGER,
                    metadata JSON,
                    metric_scores JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (eval_id) REFERENCES evaluations(eval_id),
                    FOREIGN KEY (prompt_id) REFERENCES prompts(prompt_id)
                )
                """,
            ]

            for table in tables:
                table_name = (
                    table.split("CREATE TABLE IF NOT EXISTS")[1].split("(")[0].strip()
                )
                try:
                    cursor.execute(table)
                    self.logger.debug(f"Initialized table: {table_name}")
                except sqlite3.Error as e:
                    self.logger.error(f"Error creating table {table_name}: {e}")
                    raise DatabaseError(f"Failed to create table {table_name}: {e}")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}")
        finally:
            if conn:
                conn.close()

    def create_project(self, project_id: str) -> None:
        """Create a new project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO projects (project_id) VALUES (?)", (project_id,)
                )
            except sqlite3.IntegrityError:
                raise DatabaseError(f"Project with ID {project_id} already exists")

    def project_exists(self, project_id: str) -> bool:
        """Check if a project exists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,))
            return cursor.fetchone() is not None

    def version_exists(self, project_id: str, version_id: str) -> bool:
        """Check if a version exists in a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1 
                FROM versions 
                WHERE project_id = ? AND version_id = ?
            """,
                (project_id, version_id),
            )
            return cursor.fetchone() is not None

    def create_version(self, project_id: str, version_id: str) -> None:
        """Create a new version for a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO versions (project_id, version_id)
                    VALUES (?, ?)
                """,
                    (project_id, version_id),
                )
            except sqlite3.IntegrityError as e:
                if "foreign key constraint failed" in str(e).lower():
                    raise DatabaseError(f"Project {project_id} does not exist")
                raise DatabaseError(
                    f"Version {version_id} already exists in project {project_id}"
                )

    def list_projects(self) -> List[Dict]:
        """List all projects"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT project_id, created_at
                FROM projects
                ORDER BY created_at DESC
            """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_project_versions(self, project_id: str) -> List[Dict]:
        """Get all versions for a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT version_id, created_at
                FROM versions
                WHERE project_id = ?
                ORDER BY created_at
            """,
                (project_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # Path Operations
    def add_paths_to_project(self, project_id: str, paths: List[str]) -> None:
        """Add new paths to a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for path in paths:
                try:
                    cursor.execute(
                        """
                        INSERT INTO project_paths (project_id, path)
                        VALUES (?, ?)
                    """,
                        (project_id, path),
                    )
                except sqlite3.IntegrityError:
                    self.logger.warning(
                        f"Path '{path}' already exists for project {project_id}"
                    )

    def add_paths_to_version(
        self, project_id: str, version_id: str, paths: List[str]
    ) -> None:
        """Add new paths to a version"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for path in paths:
                try:
                    cursor.execute(
                        """
                        INSERT INTO version_paths (project_id, version_id, path)
                        VALUES (?, ?, ?)
                    """,
                        (project_id, version_id, path),
                    )
                except sqlite3.IntegrityError:
                    self.logger.warning(
                        f"Path '{path}' already exists for version {version_id} in project {project_id}"
                    )

    def get_project_paths(self, project_id: str) -> List[str]:
        """Get all paths for a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT path FROM project_paths
                WHERE project_id = ?
                ORDER BY created_at
            """,
                (project_id,),
            )
            return [row[0] for row in cursor.fetchall()]

    def get_version_paths(self, project_id: str, version_id: str) -> List[str]:
        """Get all paths for a specific version in a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT path FROM version_paths
                WHERE project_id = ? AND version_id = ?
                ORDER BY created_at
            """,
                (project_id, version_id),
            )
            return [row[0] for row in cursor.fetchall()]

    # Failure Reason Operations
    def add_failure_reasons_to_project(
        self, project_id: str, reasons: List[str]
    ) -> None:
        """Add new failure reasons to a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for reason in reasons:
                try:
                    cursor.execute(
                        """
                        INSERT INTO project_failure_reasons (project_id, failure_reason)
                        VALUES (?, ?)
                    """,
                        (project_id, reason),
                    )
                except sqlite3.IntegrityError:
                    self.logger.warning(
                        f"Failure reason '{reason}' already exists for project {project_id}"
                    )

    def add_failure_reasons_to_version(
        self, project_id: str, version_id: str, reasons: List[str]
    ) -> None:
        """Add new failure reasons to a version"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for reason in reasons:
                try:
                    cursor.execute(
                        """
                        INSERT INTO version_failure_reasons (project_id, version_id, failure_reason)
                        VALUES (?, ?, ?)
                    """,
                        (project_id, version_id, reason),
                    )
                except sqlite3.IntegrityError:
                    self.logger.warning(
                        f"Failure reason '{reason}' already exists for version {version_id} in project {project_id}"
                    )

    def get_project_failure_reasons(self, project_id: str) -> List[str]:
        """Get all failure reasons for a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT failure_reason FROM project_failure_reasons
                WHERE project_id = ?
                ORDER BY created_at
            """,
                (project_id,),
            )
            return [row[0] for row in cursor.fetchall()]

    def get_version_failure_reasons(
        self, project_id: str, version_id: str
    ) -> List[str]:
        """Get all failure reasons for a specific version in a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT failure_reason FROM version_failure_reasons
                WHERE project_id = ? AND version_id = ?
                ORDER BY created_at
            """,
                (project_id, version_id),
            )
            return [row[0] for row in cursor.fetchall()]

    # Prompt Operations
    def add_project_prompts(self, project_id: str, prompt_texts: List[str]):
        """Create a new project-level prompt and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for prompt_text in prompt_texts:
                cursor.execute(
                    """
                    INSERT INTO prompts (project_id, prompt_text, prompt_type)
                    VALUES (?, ?, 'project')
                """,
                    (project_id, prompt_text),
                )

    def add_version_prompts(
        self, project_id: str, version_id: str, prompt_texts: List[str]
    ):
        """Create a new version-level prompt and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for prompt_text in prompt_texts:
                cursor.execute(
                    """
                    INSERT INTO prompts (project_id, version_id, prompt_text, prompt_type)
                    VALUES (?, ?, ?, 'version')
                """,
                    (project_id, version_id, prompt_text),
                )

    def get_project_prompts(self, project_id: str) -> List[int]:
        """Get all project-level prompt IDs for a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT prompt_id
                FROM prompts
                WHERE project_id = ? AND prompt_type = 'project'
                ORDER BY created_at
                """,
                (project_id,),
            )
            return [row[0] for row in cursor.fetchall()]

    def get_version_prompts(self, project_id: str, version_id: str) -> List[int]:
        """Get all version-level prompt IDs for a specific version in a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT prompt_id
                FROM prompts
                WHERE project_id = ? AND version_id = ? AND prompt_type = 'version'
                ORDER BY created_at
                """,
                (project_id, version_id),
            )
            return [row[0] for row in cursor.fetchall()]

    # Evaluation Operations

    def create_project_evaluation(
        self, project_id: str, metrics_dict: Optional[Dict] = None
    ) -> int:
        """Create a new project-level evaluation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evaluations (project_id, eval_type, metrics_dict)
                VALUES (?, 'project', ?)
                """,
                (
                    project_id,
                    json.dumps(metrics_dict) if metrics_dict else None,
                ),
            )
            return cursor.lastrowid

    def create_version_evaluation(
        self, project_id: str, version_id: str, metrics_dict: Optional[Dict] = None
    ) -> int:
        """Create a new version-level evaluation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evaluations (project_id, version_id, eval_type, metrics_dict)
                VALUES (?, ?, 'version', ?)
                """,
                (
                    project_id,
                    version_id,
                    json.dumps(metrics_dict) if metrics_dict else None,
                ),
            )
            return cursor.lastrowid

    def get_project_evaluations(self, project_id: str) -> List[Dict]:
        """Get all project-level evaluations for a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT eval_id, metrics_dict, created_at 
                FROM evaluations
                WHERE project_id = ? AND eval_type = 'project'
                ORDER BY created_at
                """,
                (project_id,),
            )

            return [
                {
                    "eval_id": row["eval_id"],
                    "metrics_dict": (
                        json.loads(row["metrics_dict"])
                        if row["metrics_dict"]
                        else {}
                    ),
                    "created_at": row["created_at"],
                }
                for row in cursor.fetchall()
            ]

    def get_version_evaluations(self, project_id: str, version_id: str) -> List[Dict]:
        """Get all version-level evaluations for a specific version"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT eval_id, metrics_dict, created_at 
                FROM evaluations
                WHERE project_id = ? AND version_id = ? AND eval_type = 'version'
                ORDER BY created_at
                """,
                (project_id, version_id),
            )

            return [
                {
                    "eval_id": row["eval_id"],
                    "metrics_dict": (
                        json.loads(row["metrics_dict"])
                        if row["metrics_dict"]
                        else {}
                    ),
                    "created_at": row["created_at"],
                }
                for row in cursor.fetchall()
            ]

    # Prompt Run Operations
    def create_prompt_run(
        self,
        eval_id: int,
        prompt_id: int,
        metadata: Optional[Dict] = None,
        metric_scores: Optional[Dict] = None,
    ) -> int:
        """Create a new prompt run and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get prompt type and details
            cursor.execute(
                """
                SELECT prompt_type, project_id, version_id 
                FROM prompts 
                WHERE prompt_id = ?
                """,
                (prompt_id,),
            )
            prompt_row = cursor.fetchone()
            if not prompt_row:
                raise DatabaseError(f"Prompt with ID {prompt_id} not found")

            # Get evaluation type and details
            cursor.execute(
                """
                SELECT eval_type, project_id, version_id 
                FROM evaluations 
                WHERE eval_id = ?
                """,
                (eval_id,),
            )
            eval_row = cursor.fetchone()
            if not eval_row:
                raise DatabaseError(f"Evaluation with ID {eval_id} not found")

            # Verify matching types
            if prompt_row["prompt_type"] != eval_row["eval_type"]:
                raise DatabaseError(
                    "Prompt and evaluation must be of the same type (project or version)"
                )

            # Verify project match for both types
            if prompt_row["project_id"] != eval_row["project_id"]:
                raise DatabaseError(
                    "Prompt and evaluation must belong to the same project"
                )

            # For version type, verify version match
            if (
                prompt_row["prompt_type"] == "version"
                and prompt_row["version_id"] != eval_row["version_id"]
            ):
                raise DatabaseError(
                    "Version-level prompt and evaluation must belong to the same version"
                )

            cursor.execute(
                """
                INSERT INTO prompt_runs (eval_id, prompt_id, metadata, metric_scores)
                VALUES (?, ?, ?, ?)
                """,
                (
                    eval_id,
                    prompt_id,
                    json.dumps(metadata) if metadata else None,
                    json.dumps(metric_scores) if metric_scores else None,
                ),
            )
            return cursor.lastrowid

    def get_prompt_runs(self, eval_id: int) -> List[Dict]:
        """Get all runs for an evaluation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.run_id, r.prompt_id, p.prompt_type, p.prompt_text,
                       r.metadata, r.metric_scores, r.created_at
                FROM prompt_runs r
                JOIN prompts p ON r.prompt_id = p.prompt_id
                WHERE r.eval_id = ?
                ORDER BY r.created_at
                """,
                (eval_id,),
            )

            return [
                {
                    "run_id": row["run_id"],
                    "prompt_id": row["prompt_id"],
                    "prompt_type": row["prompt_type"],
                    "prompt_text": row["prompt_text"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "metric_scores": (
                        json.loads(row["metric_scores"]) if row["metric_scores"] else {}
                    ),
                    "created_at": row["created_at"],
                }
                for row in cursor.fetchall()
            ]

    def get_run_details(self, run_id: int) -> Dict:
        """Get complete details for a specific run"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.*, p.prompt_type, p.prompt_text, p.project_id, p.version_id,
                    e.eval_type, e.metrics_dict as eval_metrics
                FROM prompt_runs r
                JOIN prompts p ON r.prompt_id = p.prompt_id
                JOIN evaluations e ON r.eval_id = e.eval_id
                WHERE r.run_id = ?
                """,
                (run_id,),
            )

            row = cursor.fetchone()
            if not row:
                raise DatabaseError(f"No run found with run_id {run_id}")

            return {
                "run_id": row["run_id"],
                "eval_id": row["eval_id"],
                "prompt_id": row["prompt_id"],
                "prompt_type": row["prompt_type"],
                "eval_type": row["eval_type"],
                "prompt_text": row["prompt_text"],
                "project_id": row["project_id"],
                "version_id": row["version_id"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "metric_scores": (
                    json.loads(row["metric_scores"]) if row["metric_scores"] else {}
                ),
                "eval_metrics": (
                    json.loads(row["eval_metrics"]) if row["eval_metrics"] else {}
                ),
                "created_at": row["created_at"],
            }
        
    def update_prompt_run(
        self,
        run_id: int,
        metric_scores: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Update metric scores and/or metadata for a prompt run"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if metric_scores is not None:
                updates.append("metric_scores = ?")
                params.append(json.dumps(metric_scores))

            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))

            if not updates:
                return

            query = f"""
                UPDATE prompt_runs
                SET {', '.join(updates)}
                WHERE run_id = ?
            """
            params.append(run_id)

            cursor.execute(query, params)

            if cursor.rowcount == 0:
                raise DatabaseError(f"No run found with run_id {run_id}")

    def clean_database(self) -> None:
        """Clean up the database by removing orphaned records"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Remove prompt runs with invalid eval_ids or prompt_ids
            cursor.execute(
                """
                DELETE FROM prompt_runs 
                WHERE eval_id NOT IN (SELECT eval_id FROM evaluations)
                OR prompt_id NOT IN (SELECT prompt_id FROM prompts)
                """
            )

            # Remove evaluations with invalid references
            cursor.execute(
                """
                DELETE FROM evaluations 
                WHERE (eval_type = 'project' AND project_id NOT IN (SELECT project_id FROM projects))
                OR (eval_type = 'version' AND (project_id, version_id) NOT IN 
                    (SELECT project_id, version_id FROM versions))
                """
            )

            self.logger.info("Database cleaned successfully")

    def get_project_summary(self, project_id: str) -> Dict:
        """Get a summary of all data related to a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get project evaluation count
            project_eval_count = cursor.execute(
                """
                SELECT COUNT(*) 
                FROM evaluations 
                WHERE project_id = ? AND eval_type = 'project'
                """,
                (project_id,),
            ).fetchone()[0]

            # Get version evaluation count
            version_eval_count = cursor.execute(
                """
                SELECT COUNT(*) 
                FROM evaluations 
                WHERE project_id = ? AND eval_type = 'version'
                """,
                (project_id,),
            ).fetchone()[0]

            # Add these counts to the existing summary
            summary = super().get_project_summary(project_id)
            summary.update(
                {
                    "project_evaluation_count": project_eval_count,
                    "version_evaluation_count": version_eval_count,
                }
            )
            return summary

    def get_version_summary(self, project_id: str, version_id: str) -> Dict:
        """Get a summary of all data related to a specific version in a project"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get version details
            cursor.execute(
                """
                SELECT created_at 
                FROM versions 
                WHERE project_id = ? AND version_id = ?
                """,
                (project_id, version_id),
            )
            version_row = cursor.fetchone()
            if not version_row:
                raise DatabaseError(
                    f"Version {version_id} not found in project {project_id}"
                )

            # Get counts
            path_count = cursor.execute(
                """
                SELECT COUNT(*) 
                FROM version_paths 
                WHERE project_id = ? AND version_id = ?
                """,
                (project_id, version_id),
            ).fetchone()[0]

            prompt_count = cursor.execute(
                """
                SELECT COUNT(*) 
                FROM prompts 
                WHERE project_id = ? AND version_id = ? AND prompt_type = 'version'
                """,
                (project_id, version_id),
            ).fetchone()[0]

            eval_count = cursor.execute(
                """
                SELECT COUNT(*) 
                FROM evaluations 
                WHERE project_id = ? AND version_id = ?
                """,
                (project_id, version_id),
            ).fetchone()[0]

            return {
                "version_id": version_id,
                "project_id": project_id,
                "created_at": version_row["created_at"],
                "path_count": path_count,
                "prompt_count": prompt_count,
                "evaluation_count": eval_count,
                "paths": self.get_version_paths(project_id, version_id),
                "failure_reasons": self.get_version_failure_reasons(
                    project_id, version_id
                ),
            }
