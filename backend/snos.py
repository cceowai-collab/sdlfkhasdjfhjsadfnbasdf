# backend/snos.py
from telethon import TelegramClient
from config import API_ID, API_HASH
import os
import re

DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sessions')


async def report(link: str) -> str:
    """
    Отправляет жалобы на сообщение с использованием всех сессий
    """
    try:
        # Отладочный вывод
        print(f"DEBUG: API_ID={API_ID} (type: {type(API_ID)})")
        print(f"DEBUG: API_HASH={API_HASH} (type: {type(API_HASH)})")

        # Очищаем ссылку
        link = link.strip()

        # Проверяем ссылку
        if 't.me/' not in link and 'telegram.me/' not in link:
            return "❌ Неверный формат ссылки. Используйте: https://t.me/username/123"

        # Парсим ссылку
        pattern = r'(?:https?://)?(?:t\.me|telegram\.me)/([^/]+)/(\d+)'
        match = re.search(pattern, link)

        if not match:
            return "❌ Неверный формат ссылки. Пример: https://t.me/username/123"

        username = match.group(1)
        message_id = int(match.group(2))

        print(f"✅ Ссылка распарсена: username={username}, message_id={message_id}")

        # Проверяем папку с сессиями
        if not os.path.exists(DIRECTORY):
            os.makedirs(DIRECTORY, exist_ok=True)
            return "❌ Папка с сессиями не найдена. Создана новая папка."

        # Получаем список сессий
        sessions = [session for session in os.listdir(DIRECTORY) if session.endswith('.session')]

        if not sessions:
            return "❌ Нет сессий для отправки жалоб. Добавьте .session файлы в папку sessions/"

        successful_reports = 0
        errors = []

        for session_file in sessions:
            print(f"🔑 Используется сессия: {session_file}")

            session_path = os.path.join(DIRECTORY, session_file)

            # Проверяем, что путь не содержит спецсимволов
            print(f"DEBUG: session_path={session_path}")

            # Инициализируем клиент с явными параметрами
            try:
                client = TelegramClient(
                    session=session_path,
                    api_id=int(API_ID),  # Явно приводим к int
                    api_hash=str(API_HASH)  # Явно приводим к str
                )
            except Exception as e:
                errors.append(f"Ошибка инициализации {session_file}: {str(e)[:50]}")
                print(f"❌ Ошибка инициализации {session_file}: {e}")
                continue

            try:
                await client.connect()

                if not await client.is_user_authorized():
                    errors.append(f"Сессия {session_file} не авторизована")
                    print(f"⚠️ Сессия {session_file} не авторизована")
                    continue

                # Получаем чат
                try:
                    chat = await client.get_entity(username)
                    print(f"✅ Чат найден: {chat}")
                except Exception as e:
                    errors.append(f"Не найден чат @{username}: {str(e)[:30]}")
                    print(f"❌ Не найден чат @{username}: {e}")
                    continue

                # Отправляем жалобу
                from telethon.tl.functions.messages import ReportRequest

                await client(ReportRequest(
                    peer=chat,
                    id=[message_id],
                    reason='spam',
                    message=''
                ))

                print(f"✅ Жалоба отправлена с сессии {session_file}")
                successful_reports += 1

            except Exception as e:
                error_msg = str(e)
                errors.append(f"Сессия {session_file}: {error_msg[:50]}")
                print(f"❌ Ошибка с сессией {session_file}: {e}")
            finally:
                try:
                    await client.disconnect()
                except:
                    pass

        # Формируем отчет
        if successful_reports == 0:
            error_text = '\n'.join(errors[:5]) if errors else "Неизвестная ошибка"
            return f"❌ Не удалось отправить жалобы\n\nОшибки (первые 5):\n{error_text}"
        else:
            result = f"✅ Успешно отправлено: {successful_reports}"
            if errors:
                result += f"\n❌ Всего ошибок: {len(errors)}"
                result += f"\n\nПервые 5 ошибок:\n" + '\n'.join(errors[:5])
            return result

    except Exception as e:
        return f"❌ Критическая ошибка: {e}"