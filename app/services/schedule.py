from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..models.schedule import Group, Day, Lesson, User
from sqlalchemy import text
import hashlib, hmac
from urllib.parse import parse_qsl
from ..core.config import settings

class AuthHelpers:
    @staticmethod
    def _parse_user_payload(init_data: str) -> dict | None:
        try:
            data = dict(parse_qsl(
                init_data,
                keep_blank_values=True,
                strict_parsing=False,
                encoding='utf-8',
                errors='ignore'
            ))
            # try parse user json
            user = data.get('user')
            if user:
                import json
                u = json.loads(user)
                return {
                    "user_id": int(u.get('id')) if u.get('id') is not None else None,
                    "username": u.get('username'),
                    "first_name": u.get('first_name'),
                    "last_name": u.get('last_name'),
                    "language_code": u.get('language_code')
                }
            if 'user_id' in data:
                return {"user_id": int(data['user_id'])}
        except Exception:
            pass
        return None

    @staticmethod
    def verify_init_data(init_data: str) -> dict | None:
        # В публичном режиме не проверяем HMAC, но пытаемся извлечь реальные данные пользователя
        if settings.ALLOW_PUBLIC:
            if not init_data:
                return {"user_id": "public"}
            payload = AuthHelpers._parse_user_payload(init_data)
            return payload or {"user_id": "public"}

        # Строгая проверка в обычном режиме
        if not init_data or not settings.BOT_TOKEN:
            return None
        data = dict(parse_qsl(init_data, strict_parsing=True))
        hash_ = data.pop('hash', None)
        dcs = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))
        secret = hashlib.sha256(settings.BOT_TOKEN.encode()).digest()
        check = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
        if check != hash_:
            return None
        # try parse user json
        user = data.get('user')
        try:
            import json
            if user:
                u = json.loads(user)
                return {
                    "user_id": int(u.get('id')),
                    "username": u.get('username'),
                    "first_name": u.get('first_name'),
                    "last_name": u.get('last_name'),
                    "language_code": u.get('language_code')
                }
        except Exception:
            pass
        if 'user_id' in data:
            return {"user_id": int(data['user_id'])}
        return None

    @staticmethod
    def upsert_user(db: Session, payload: dict) -> User | None:
        try:
            uid = payload.get('user_id')
            if not uid or uid == 'public':
                return None
            user = db.query(User).filter(User.tg_user_id == uid).first()
            if not user:
                user = User(tg_user_id=uid)
                db.add(user)
            user.username = payload.get('username', user.username)
            user.first_name = payload.get('first_name', user.first_name)
            user.last_name = payload.get('last_name', user.last_name)
            user.language_code = payload.get('language_code', user.language_code)
            from datetime import datetime
            user.last_seen_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            print("upsert user error", e)
            db.rollback()
            return None

    @staticmethod
    def save_last_selection(db: Session, user_id: int, group_id: int | None = None, teacher: str | None = None):
        user = db.query(User).filter(User.tg_user_id == user_id).first()
        if not user:
            return
        if group_id is not None:
            user.last_selected_group_id = group_id
        if teacher is not None:
            user.last_selected_teacher = teacher
        db.commit()

class ScheduleService:
    @staticmethod
    def get_group_by_id(db: Session, group_id: int) -> Optional[Group]:
        return db.query(Group).filter(Group.id == group_id).first()
    
    @staticmethod
    def get_schedule_by_date(db: Session, group_id: int, date: str) -> Optional[Day]:
        try:
            # Прямой SQL запрос для получения дня и уроков
            query = text(
                """
                SELECT d.id, d.date, d.group_id, l.id as lesson_id, l.time, l.subject, l.type, l.classroom, l.teacher
                FROM days d
                LEFT JOIN lessons l ON l.day_id = d.id
                WHERE d.group_id = :group_id AND d.date LIKE :date
                ORDER BY l.time ASC
                """
            )
            # Преобразуем ISO YYYY-MM-DD в шаблон ДД.ММ.ГГГГ (часть строки)
            try:
                yyyy, mm, dd = date.split("-")
                formatted_like = f"%{dd}.{mm}.{yyyy}%"
            except Exception:
                formatted_like = f"%{date}%"
            result = db.execute(query, {"group_id": group_id, "date": formatted_like})
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
                        for row in schedule_data if row[3] is not None
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
    
    @staticmethod
    def get_all_teachers(db: Session) -> list:
        # Получаем уникальные имена преподавателей из lessons
        result = db.execute(text("SELECT DISTINCT teacher FROM lessons WHERE teacher IS NOT NULL AND teacher != '' ORDER BY teacher ASC"))
        teachers = [{"name": row[0]} for row in result]
        return teachers
    
    @staticmethod
    def get_teacher_schedule_by_date(db: Session, teacher_name: str, date: str) -> Optional[dict]:
        try:
            # Прямой SQL запрос для получения уроков преподавателя на дату
            query = text(
                """
                SELECT l.id, l.day_id, l.time, l.subject, l.type, l.classroom, l.teacher, d.date, d.group_id
                FROM lessons l
                JOIN days d ON l.day_id = d.id
                WHERE l.teacher = :teacher_name AND d.date LIKE :date
                ORDER BY l.time ASC
                """
            )
            try:
                yyyy, mm, dd = date.split("-")
                formatted_like = f"%{dd}.{mm}.{yyyy}%"
            except Exception:
                formatted_like = f"%{date}%"
            result = db.execute(query, {"teacher_name": teacher_name, "date": formatted_like})
            lessons_data = result.fetchall()
            if lessons_data:
                return {
                    "date": lessons_data[0][7],
                    "teacher": teacher_name,
                    "lessons": [
                        {
                            "id": row[0],
                            "day_id": row[1],
                            "time": row[2],
                            "subject": row[3],
                            "type": row[4],
                            "classroom": row[5],
                            "teacher": row[6],
                            "group_id": row[8]
                        }
                        for row in lessons_data
                    ]
                }
            return None
        except Exception as e:
            print(f"Ошибка получения расписания преподавателя: {e}")
            return None
    
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