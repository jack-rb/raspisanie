from app.core.database import Base, engine, SessionLocal
from app.models.schedule import Group, Day, Lesson
from datetime import datetime

def init_database():
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Создаем группу
        group = Group(name="ИБ-11")
        db.add(group)
        db.flush()
        
        # Создаем день
        day = Day(date=datetime.now().date(), group_id=group.id)
        db.add(day)
        db.flush()
        
        # Добавляем пары
        lessons = [
            Lesson(
                day_id=day.id,
                time="09:55 - 11:30",
                subject="Мультисервисные сети связи",
                type="Лекционные занятия",
                classroom="315",
                teacher="Лихтциндер Борис Яковлевич"
            )
        ]
        
        for lesson in lessons:
            db.add(lesson)
        
        db.commit()
        print("База данных успешно создана и заполнена")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database() 