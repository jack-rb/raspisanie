from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from ..core.database import Base

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
