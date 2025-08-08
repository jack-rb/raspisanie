import random
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.schedule import Group, Day, Lesson

# Данные для генерации
GROUPS = [f"{chr(1040+i)}группа{i+1}" for i in range(5)]  # Агруппа1, Бгруппа2, ...
TEACHERS = [f"{chr(1040+i)}.Фамилия Имя Отчество" for i in range(5)]  # А.Фамилия Имя Отчество, ...
SUBJECTS = ["Математика", "Физика", "Информатика", "История", "Литература", "Биология", "Химия", "География"]
CLASSROOMS = ["101", "202", "303", "404", "505", "606"]
TYPES = ["Лекция", "Практика", "Семинар"]

START_DATE = datetime(2025, 7, 10)
END_DATE = datetime(2025, 8, 10)


def fill_test_data():
    db = SessionLocal()
    # Очистка таблиц
    db.query(Lesson).delete()
    db.query(Day).delete()
    # db.query(Group).delete()  # Не удаляем группы, чтобы не терять существующие
    db.commit()
    # Создаём группы, если их нет
    group_objs = []
    for name in GROUPS:
        group = db.query(Group).filter_by(name=name).first()
        if not group:
            group = Group(name=name)
            db.add(group)
            db.commit()
            db.refresh(group)
        group_objs.append(group)

    # Создаём дни и уроки
    current_date = START_DATE
    while current_date <= END_DATE:
        for group in group_objs:
            day = Day(date=current_date.date(), group_id=group.id)
            db.add(day)
            db.flush()  # чтобы получить day.id
            lessons_count = random.randint(2, 4)
            used_teachers = random.sample(TEACHERS, k=lessons_count)
            for i in range(lessons_count):
                lesson = Lesson(
                    day_id=day.id,
                    time=f"{9+i*2:02d}:00-{10+i*2:02d}:30",
                    subject=random.choice(SUBJECTS),
                    type=random.choice(TYPES),
                    classroom=random.choice(CLASSROOMS),
                    teacher=used_teachers[i]
                )
                db.add(lesson)
        current_date += timedelta(days=1)
    db.commit()
    db.close()
    print("Тестовые данные успешно добавлены!")

if __name__ == "__main__":
    fill_test_data() 