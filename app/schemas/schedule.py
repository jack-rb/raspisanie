from pydantic import BaseModel
from typing import List, Optional

class LessonBase(BaseModel):
    time: str
    subject: str
    type: str
    classroom: Optional[str] = None
    teacher: Optional[str] = None

class LessonCreate(LessonBase):
    day_id: int

class Lesson(LessonBase):
    id: int
    day_id: int

    class Config:
        from_attributes = True

class DayBase(BaseModel):
    date: str
    group_id: int

class DayCreate(DayBase):
    pass

class Day(DayBase):
    id: int
    lessons: List[Lesson] = []

    class Config:
        from_attributes = True

class Group(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class Teacher(BaseModel):
    name: str

    class Config:
        from_attributes = True 