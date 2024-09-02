from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Glyph(Base):
    __tablename__ = "glyph"

    id: Mapped[int] = mapped_column(primary_key=True)
    glyph_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    unicode: Mapped[int] = mapped_column(nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    meanings: Mapped[list[Meaning]] = relationship(back_populates="glyph", cascade="all, delete-orphan")
    guesses: Mapped[list[Guess]] = relationship(back_populates="glyph", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Glyph {self.glyph_id}>"


class Meaning(Base):
    __tablename__ = "meaning"

    id: Mapped[int] = mapped_column(primary_key=True)
    phrase: Mapped[str] = mapped_column(nullable=False)

    glyph_id: Mapped[int] = mapped_column(ForeignKey("glyph.id"), nullable=False)
    glyph: Mapped[Glyph] = relationship(back_populates="meanings")

    def __repr__(self):
        return f"<Meaning {self.phrase}>"


class Guess(Base):
    __tablename__ = "guess"

    id: Mapped[int] = mapped_column(primary_key=True)
    guess_text: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    ip_address: Mapped[str] = mapped_column(nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    glyph_id: Mapped[int] = mapped_column(ForeignKey("glyph.id"), nullable=False)
    glyph: Mapped[Glyph] = relationship(back_populates="guesses")

    def __repr__(self):
        return f"<Guess {self.guess_text}>"


class BannedIP(Base):
    __tablename__ = "banned_ip"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip_address: Mapped[str] = mapped_column(nullable=False, unique=True)
    banned_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<BannedIP {self.ip_address}>"
