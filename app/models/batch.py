from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class Batch(Base):
    __tablename__ = "batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    total = Column(Integer, nullable=False)
    completed = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="running")  # running | done | partial
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
