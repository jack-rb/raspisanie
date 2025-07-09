from sqlalchemy import create_engine
from app.models.schedule import Group, Day, Lesson
from sqlalchemy.orm import sessionmaker

# SQLite подключение (локальное)
sqlite_url = "sqlite:///./schedule.db"
sqlite_engine = create_engine(sqlite_url)
SQLiteSession = sessionmaker(bind=sqlite_engine)

# MySQL подключение (на сервере)
mysql_url = "mysql+aiomysql://u2973600_admin:ваш_пароль@localhost/u2973600_schedule"
mysql_engine = create_engine(mysql_url)
MySQLSession = sessionmaker(bind=mysql_engine)

def migrate_data():
    # Создаем сессии
    sqlite_session = SQLiteSession()
    mysql_session = MySQLSession()
    
    try:
        # Переносим группы
        groups = sqlite_session.query(Group).all()
        for group in groups:
            new_group = Group(
                id=group.id,
                name=group.name
            )
            mysql_session.add(new_group)
        
        # Переносим дни
        days = sqlite_session.query(Day).all()
        for day in days:
            new_day = Day(
                id=day.id,
                date=day.date,
                group_id=day.group_id
            )
            mysql_session.add(new_day)
            
        # Переносим пары
        lessons = sqlite_session.query(Lesson).all()
        for lesson in lessons:
            new_lesson = Lesson(
                id=lesson.id,
                day_id=lesson.day_id,
                time=lesson.time,
                subject=lesson.subject,
                type=lesson.type,
                classroom=lesson.classroom,
                teacher=lesson.teacher
            )
            mysql_session.add(new_lesson)
            
        mysql_session.commit()
        print("Данные успешно перенесены")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        mysql_session.rollback()
    finally:
        sqlite_session.close()
        mysql_session.close()

if __name__ == "__main__":
    migrate_data() 