from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.schedule import Group, Day, Lesson

def import_data():
    db = SessionLocal()
    try:
        # Создаем группу
        group = Group(name="ИС-31")
        db.add(group)
        db.flush()

        # Создаем расписание на несколько дней
        for i in range(3):  # На 3 дня
            day_date = datetime.now().date() + timedelta(days=i)
            day = Day(date=day_date, group_id=group.id)
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
                ),
                Lesson(
                    day_id=day.id,
                    time="11:40 - 13:15",
                    subject="Мультисервисные сети связи",
                    type="Лекционные занятия",
                    classroom="315",
                    teacher="Лихтциндер Борис Яковлевич"
                ),
                Lesson(
                    day_id=day.id,
                    time="13:35 - 15:10",
                    subject="Сети и системы передачи информации",
                    type="Лекционные занятия",
                    classroom="315",
                    teacher="Васин Николай Николаевич"
                )
            ]
            
            for lesson in lessons:
                db.add(lesson)
        
        db.commit()
        print("Данные импортированы успешно")
        
    except Exception as e:
        print(f"Ошибка при импорте данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_data()