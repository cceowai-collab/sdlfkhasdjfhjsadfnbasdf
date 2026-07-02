# backend/database.py
import aiosqlite
import os
from datetime import datetime, timedelta

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, 'database')
os.makedirs(DB_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(DB_DIR, 'database.db')

async def createDatabase():
    """Создает базу данных и таблицу"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as con:
            await con.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    userid INTEGER PRIMARY KEY,
                    sub BOOLEAN,
                    date TEXT
                )
            ''')
            await con.commit()
            print("✅ Database and table checked/created")
    except Exception as e:
        print(f"Error in createDatabase: {e}")

async def init_db():
    """Инициализация базы данных (алиас)"""
    await createDatabase()

async def checkUser(userid):
    """Проверяет пользователя в БД"""
    print(f"Checking user {userid} in the database...")
    try:
        async with aiosqlite.connect(DATABASE_PATH) as con:
            async with con.execute("SELECT userid FROM users WHERE userid = ?", (userid,)) as cur:
                row = await cur.fetchone()
                if row:
                    print(f"User {userid} found")
                    return True
                print(f"User {userid} not found, creating new user")
                await newUser(userid)
                return False
    except Exception as e:
        print(f"Error in checkUser: {e}")
        return False

async def newUser(userid):
    """Создает нового пользователя"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as con:
            await con.execute("INSERT INTO users (userid, sub, date) VALUES (?, ?, ?)", (userid, False, None))
            await con.commit()
            print(f"New user {userid} added to the database")
    except Exception as e:
        print(f"Error in newUser: {e}")

async def giveSub(userid, days):
    """Выдает подписку"""
    try:
        date = datetime.now() + timedelta(days=int(days))
        async with aiosqlite.connect(DATABASE_PATH) as con:
            await con.execute("UPDATE users SET sub = ?, date = ? WHERE userid = ?", (True, date.isoformat(), userid))
            await con.commit()
            print(f"Subscription given to {userid} for {days} days")
    except Exception as e:
        print(f"Error in giveSub: {e}")

async def closeSub(userid):
    """Закрывает подписку"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as con:
            await con.execute("UPDATE users SET sub = ?, date = ? WHERE userid = ?", (False, None, userid))
            await con.commit()
            print(f"Subscription closed for user {userid}")
    except Exception as e:
        print(f"Error in closeSub: {e}")

async def checkSubStatus(userid):
    """Проверяет статус подписки"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as con:
            async with con.execute("SELECT sub FROM users WHERE userid = ?", (userid,)) as cur:
                row = await cur.fetchone()
                if row:
                    return bool(row[0])
                return False
    except Exception as e:
        print(f"Error in checkSubStatus: {e}")
        return False

async def checkSubDate(userid):
    """Проверяет дату подписки"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as con:
            async with con.execute("SELECT date FROM users WHERE userid = ?", (userid,)) as cur:
                row = await cur.fetchone()
                if row and row[0]:
                    expiration_date = datetime.fromisoformat(row[0])
                    if expiration_date <= datetime.now():
                        await closeSub(userid)
                        return False
                    return True
                return False
    except Exception as e:
        print(f"Error in checkSubDate: {e}")
        return False

async def subDate(userid):
    """Возвращает дату окончания подписки"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as con:
            async with con.execute("SELECT date FROM users WHERE userid = ?", (userid,)) as cur:
                row = await cur.fetchone()
                if row and row[0]:
                    return datetime.fromisoformat(row[0])
                return None
    except Exception as e:
        print(f"Error in subDate: {e}")
        return None

async def updateSubStatus(userid, status):
    """Обновляет статус подписки в БД"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as con:
            await con.execute("UPDATE users SET sub = ? WHERE userid = ?", (status, userid))
            await con.commit()
            print(f"Subscription status updated for {userid} to {status}")
    except Exception as e:
        print(f"Error in updateSubStatus: {e}")
