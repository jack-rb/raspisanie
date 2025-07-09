from sqlalchemy import create_engine, text
from app.core.config import settings

def inspect_tables():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as connection:
        # Проверяем группы
        result = connection.execute(text("SELECT * FROM groups"))
        print("\nТаблица groups:")
        for row in result:
            print(row)
        
        # Проверяем дни
        result = connection.execute(text("SELECT * FROM days"))
        print("\nТаблица days:")
        for row in result:
            print(row)
        
        # Проверяем пары
        result = connection.execute(text("SELECT * FROM lessons"))
        print("\nТаблица lessons:")
        for row in result:
            print(row)

if __name__ == "__main__":
    inspect_tables()
