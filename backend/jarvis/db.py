from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    create_engine,
    event,
)


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc)


class Store:
    def __init__(self, url):
        self.pg = url.startswith("postgresql")
        self.engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args=(
                {"check_same_thread": False} if not self.pg else {"connect_timeout": 8}
            ),
            **({"pool_size": 3, "max_overflow": 2} if self.pg else {})
        )
        if not self.pg:

            @event.listens_for(self.engine, "connect")
            def foreign_keys(conn, _):
                conn.execute("PRAGMA foreign_keys=ON")

        m = MetaData(schema="jarvis" if self.pg else None)
        self.metadata = m

        def fk(t):
            return ForeignKey(("jarvis." if self.pg else "") + t)

        self.users = Table(
            "users",
            m,
            Column("id", String(36), primary_key=True),
            Column("name", String(120), nullable=False),
            Column("role", String(20), nullable=False),
            Column("token_hash", String(64), unique=True, nullable=False),
            Column("active", Boolean, nullable=False, default=True),
            Column("created_at", DateTime(timezone=True), default=now),
        )
        self.conversations = Table(
            "conversations",
            m,
            Column("id", String(36), primary_key=True),
            Column("user_id", String(36), fk("users.id"), nullable=False, index=True),
            Column("title", String(120), nullable=False),
            Column("created_at", DateTime(timezone=True), default=now),
        )
        self.messages = Table(
            "messages",
            m,
            Column("id", String(36), primary_key=True),
            Column(
                "conversation_id",
                String(36),
                fk("conversations.id"),
                nullable=False,
                index=True,
            ),
            Column("role", String(20), nullable=False),
            Column("content", Text, nullable=False),
            Column("payload", JSON, nullable=False, default=dict),
            Column("created_at", DateTime(timezone=True), default=now),
        )
        self.memories = Table(
            "memories",
            m,
            Column("id", String(36), primary_key=True),
            Column("author_id", String(36), fk("users.id"), nullable=False),
            Column("base_code", String(40), nullable=False, index=True),
            Column("indicator", String(30), nullable=False),
            Column("occurred_on", String(10), nullable=False, index=True),
            Column("explanation", Text, nullable=False),
            Column("status", String(30), nullable=False),
            Column("evidence", JSON, nullable=False),
            Column("actions", Text, nullable=False),
            Column("outcome", Text, nullable=False),
            Column("metrics", JSON, nullable=False),
            Column("version", Integer, nullable=False, default=1),
            Column("confirmed_by", String(36), fk("users.id")),
            Column("confirmed_at", DateTime(timezone=True)),
            Column("created_at", DateTime(timezone=True), default=now),
        )
        self.revisions = Table(
            "memory_revisions",
            m,
            Column("id", String(36), primary_key=True),
            Column(
                "memory_id", String(36), fk("memories.id"), nullable=False, index=True
            ),
            Column("actor_id", String(36), fk("users.id"), nullable=False),
            Column("snapshot", JSON, nullable=False),
            Column("reason", Text, nullable=False),
            Column("created_at", DateTime(timezone=True), default=now),
        )
        self.audit = Table(
            "audit",
            m,
            Column("id", String(36), primary_key=True),
            Column("actor_id", String(36), fk("users.id")),
            Column("action", String(80), nullable=False),
            Column("target", String(80)),
            Column("details", JSON, nullable=False, default=dict),
            Column("created_at", DateTime(timezone=True), default=now, index=True),
        )
        self.investigations = Table(
            "investigations",
            m,
            Column("id", String(36), primary_key=True),
            Column("actor_id", String(36), fk("users.id"), nullable=False),
            Column("city", String(120), nullable=False),
            Column("start", String(10), nullable=False),
            Column("end", String(10), nullable=False),
            Column("result", JSON, nullable=False),
            Column("created_at", DateTime(timezone=True), default=now),
        )
        if not self.pg:
            m.create_all(self.engine)

    def record(self, conn, actor, action, target=None, details=None):
        conn.execute(
            self.audit.insert().values(
                id=uid(),
                actor_id=actor,
                action=action,
                target=target,
                details=details or {},
            )
        )
