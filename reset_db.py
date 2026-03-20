from app.db.session import engine, Base
from app.models.agent import Agent
from app.models.user import User

def reset_agents_table():
    print("Dropping agents table...")
    Agent.__table__.drop(engine, checkfirst=True)
    print("Creating agents table with new schema...")
    Agent.__table__.create(engine)
    print("Done!")

if __name__ == "__main__":
    reset_agents_table()
