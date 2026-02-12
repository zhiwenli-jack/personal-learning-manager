from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT id, title, status FROM materials ORDER BY id DESC LIMIT 5'))
    for row in result:
        print(f'ID:{row[0]} | {row[1]} | {row[2]}')
