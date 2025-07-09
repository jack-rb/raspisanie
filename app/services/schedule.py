from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..models.schedule import Group, Day, Lesson
from sqlalchemy import text

class ScheduleService:
    @staticmethod
    def get_group_by_id(db: Session, group_id: int) -> Optional[Group]:
        return db.query(Group).filter(Group.id == group_id).first()
    
    @staticmethod
    def get_schedule_by_date(db: Session, group_id: int, date: str) -> Optional[Day]:
        try:
            # Прямой SQL запрос для получения дня и уроков
            query = text("""
                SELECT d.id, d.date, d.group_id, l.id as lesson_id, l.time, l.subject, l.type, l.classroom, l.teacher
                FROM days d
                LEFT JOIN lessons l ON l.day_id = d.id
                WHERE d.group_id = :group_id AND d.date LIKE :date
            """)
            
            formatted_date = f"%{date.split('-')[2]}.{date.split('-')[1]}.{date.split('-')[0]}"
            result = db.execute(query, {"group_id": group_id, "date": formatted_date})
            
            schedule_data = result.fetchall()
            print("Данные расписания:", schedule_data)  # Отладка
            
            if schedule_data:
                return {
                    "id": schedule_data[0][0],
                    "date": schedule_data[0][1],
                    "group_id": schedule_data[0][2],
                    "lessons": [
                        {
                            "id": row[3],
                            "day_id": row[0],
                            "time": row[4],
                            "subject": row[5],
                            "type": row[6],
                            "classroom": row[7],
                            "teacher": row[8]
                        }
                        for row in schedule_data if row[4] is not None
                    ]
                }
            return None
        except Exception as e:
            print(f"Ошибка получения расписания: {e}")
            return None
    
    @staticmethod
    def get_lessons_by_day_id(db: Session, day_id: int) -> List[Lesson]:
        return db.query(Lesson).filter(Lesson.day_id == day_id).all()
    
    @staticmethod
    def get_all_groups(db: Session) -> List[Group]:
        # Простой запрос - только id и name групп
        result = db.execute(text("SELECT id, name FROM groups"))
        groups = [{"id": row[0], "name": row[1]} for row in result]
        print("Группы из БД:", groups)  # Отладка
        return groups
    
    def create_test_data(db: Session):
        # Создаем группу
        group = Group(name="ИС-31")
        db.add(group)
        db.flush()
        
        # Создаем день
        today = datetime.now().date()
        day = Day(date=today, group_id=group.id)
        db.add(day)
        db.flush()
        
        # Добавляем пары
        lessons = [
            Lesson(
                day_id=day.id,
                time="09:00-10:30",
                subject="Математика",
                type="Лекция",
                classroom="301",
                teacher="Иванов И.И."
            ),
            Lesson(
                day_id=day.id,
                time="10:40-12:10", 
                subject="Программирование",
                type="Практика", 
                classroom="404",
                teacher="Петров П.П."
            )
        ]
        
        for lesson in lessons:
            db.add(lesson)
        
        db.commit() 