from core.database import SessionLocal, init_db
from models.user import User
from core.auth import hash_password

def seed():
    init_db()
    db = SessionLocal()
    user = db.query(User).filter(User.username == "harris-admin").first()
    if user:
        user.hashed_password = hash_password("admin")
        print("Updated existing harris-admin user password.")
    else:
        user = User(username="harris-admin", hashed_password=hash_password("admin"))
        db.add(user)
        print("Created new harris-admin user.")
    db.commit()
    db.close()

if __name__ == "__main__":
    seed()
