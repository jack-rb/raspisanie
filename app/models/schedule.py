from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, BigInteger
from sqlalchemy.orm import relationship
from ..core.database import Base
from datetime import datetime

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    days = relationship("Day", back_populates="group")

class Day(Base):
    __tablename__ = "days"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("Group", back_populates="days")
    lessons = relationship("Lesson", back_populates="day")

class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("days.id"))
    time = Column(String)
    subject = Column(String)
    type = Column(String)
    classroom = Column(String)
    teacher = Column(String)
    day = relationship("Day", back_populates="lessons")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tg_user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_code = Column(String, nullable=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_selected_group_id = Column(Integer, nullable=True)
    last_selected_teacher = Column(String, nullable=True)
