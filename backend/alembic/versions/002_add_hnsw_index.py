"""Add HNSW index for text_vectors embedding column.

Why m=24: For 768-dim vectors, higher connectivity improves recall in sparse
high-dimensional space. 24 is the sweet spot — beyond 32, diminishing returns.

Why ef_construction=128: Favors index quality (recall) over build speed.
Plagiarism detection cannot afford false negatives.

Revision ID: 002
Revises: 001
Create Date: 2026-04-09
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_text_vectors_embedding_hnsw
        ON text_vectors
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 24, ef_construction = 128);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_text_vectors_embedding_hnsw;")
