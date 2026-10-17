import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3

# BotFather'dan olgan tokeningizni qo'shtirnoq ichiga yozing
TOKEN = 8722274230:AAFk6Pf0zWYSKKgFRrkaRWGtvzMN4sy1Sbo

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def init_db():
    conn = sqlite3.connect("guppa_game.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance_guppa INTEGER DEFAULT 0,
            silver_star INTEGER DEFAULT 0,
            gold_star INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 0,
            last_login TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER,
            invited_id INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_collection_items (
            user_id INTEGER,
            collection_id INTEGER,
            item_index INTEGER,
            UNIQUE(user_id, collection_id, item_index)
        )
    """)
    conn.commit()
    conn.close()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    args = message.text.split()
    
    conn = sqlite3.connect("guppa_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not user:
        cursor.execute("INSERT INTO users (user_id, username, balance_guppa, streak_days, last_login) VALUES (?, ?, ?, ?, ?)",
                       (user_id, username, 1, 1, today))
        conn.commit()
        
        if len(args) > 1:
            try:
                referrer_id = int(args[1])
                if referrer_id != user_id:
                    cursor.execute("SELECT * FROM referrals WHERE referrer_id = ? AND invited_id = ?", (referrer_id, user_id))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO referrals (referrer_id, invited_id) VALUES (?, ?)", (referrer_id, user_id))
                        cursor.execute("UPDATE users SET balance_guppa = balance_guppa + 1 WHERE user_id = ?", (referrer_id,))
                        conn.commit()
                        await bot.send_message(referrer_id, "🎉 Tabriklaymiz! Yangi do'stingiz qo'shildi va sizga 1 ta guppa taqdim etildi!")
            except ValueError:
                pass
        
        await message.answer("🎮 'Guppa' o'yiniga xush kelibsiz!\nSizga boshlang'ich 1 ta guppa berildi.")
    else:
        last_login_str = user[6]
        streak = user[5]
        balance = user[2]
        silver = user[3]
        gold = user[4]
        
        last_login = datetime.strptime(last_login_str, "%Y-%m-%d") if last_login_str else datetime.now()
        current_date = datetime.strptime(today, "%Y-%m-%d")
        diff = (current_date - last_login).days
        
        if diff == 1:
            streak += 1
            balance += 1
            if streak == 7:
                silver += 1
                await message.answer("🌟 7 kunlik streak! Sizga 1 ta Kumush yulduzchali guppa sovg'a qilindi!")
            elif streak == 30:
                gold += 1
                await message.answer("🏆 30 kunlik sodiqlik! Sizga 1 ta Oltin yulduzchali guppa sovg'a qilindi!")
        elif diff > 1:
            streak = 1
            
        cursor.execute("""
            UPDATE users SET balance_guppa = ?, silver_star = ?, gold_star = ?, streak_days = ?, last_login = ? 
            WHERE user_id = ?
        """, (balance, silver, gold, streak, today, user_id))
        conn.commit()
        
        await message.answer(f"Xush kelibsiz! 🔄 Streak: {streak} kun.\n📦 Oddiy guppalar: {balance} ta")
    conn.close()

@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("guppa_game.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance_guppa, silver_star, gold_star, streak_days FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        await message.answer(f"📊 Sizning hisobingiz:\n\n• Oddiy guppalar: {user[0]} ta\n• Kumush yulduzchalar: {user[1]} ta\n• Oltin yulduzchalar: {user[2]} ta\n• Kunlik streak: {user[3]} kun")
    else:
        await message.answer("Avval /start buyrug'ini bosing.")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
