"""Tabelle "manuali" di HomeHub: menu scolastico e piano allenamenti."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class SchoolMenuEntry(Base):
    __tablename__ = "school_menu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start_date: Mapped[date] = mapped_column(Date, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0 = lunedì ... 6 = domenica
    meal_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TrainingSession(Base):
    __tablename__ = "training_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start_date: Mapped[date] = mapped_column(Date, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer)
    session_text: Mapped[str] = mapped_column(Text)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AppConfig(Base):
    """Config runtime non sensibile (i secret restano in .env, mai qui)."""

    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
