from app.core.database import Base, engine
from app.models.schedule import Group, Day, Lesson

def create_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("База данных создана успешно")

if __name__ == "__main__":
    create_database()