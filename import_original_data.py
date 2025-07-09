from datetime import datetime
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

        # Создаем день
        today = datetime.now().date()
        day = Day(date=today, group_id=group.id)
        db.add(day)
        db.flush()

        # Добавляем пары из вашей оригинальной базы
        lessons = [
            Lesson(
                day_id=day.id,
                time="13:35                - 15:10",
                subject="Антенны и распространение радиоволн",
                type="Лекционные занятия",
                classroom="2-02-04",
                teacher="Кубанов Виктор Павлович"
            ),
            Lesson(
                day_id=day.id,
                time="15:20                - 16:55",
                subject="Защита информации от утечки по техническим каналам",
                type="Лекционные занятия",
                classroom="2-02-03",
                teacher="Макаров Игорь Сергеевич"
            ),
            # Добавьте остальные пары из вашей оригинальной базы
        ]
        
        for lesson in lessons:
            db.add(lesson)
        
        db.commit()
        print("Оригинальные данные восстановлены успешно")
        
    except Exception as e:
        print(f"Ошибка при импорте данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_data() 