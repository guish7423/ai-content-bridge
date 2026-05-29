"""AI Content Bridge — SQLite models for history persistence."""

import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

Base = declarative_base()


class Conversion(Base):
    """Stores a content bridge conversion."""
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True)
    original_text = Column(Text, nullable=False)
    analysis_json = Column(Text, default="{}")
    localized_text = Column(Text, default="")
    platform_results = Column(Text, default="{}")  # JSON: {x: content, linkedin: content, ...}
    usage_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "original_text": self.original_text[:200],
            "localized_text": self.localized_text[:200],
            "platforms": list(json.loads(self.platform_results or "{}").keys()),
            "cost_usd": json.loads(self.usage_json or "{}").get("cost_usd", 0),
            "tokens": json.loads(self.usage_json or "{}").get("tokens", 0),
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


engine = create_engine(settings.database_url, echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
