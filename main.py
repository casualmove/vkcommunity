import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import time

# Настройки
GROUP_ID = ''  # ID вашего сообщества (без минуса)
GROUP_TOKEN = ''  # Токен сообщества
ADMIN_ID = ''  # Ваш ID ВКонтакте (для управления ботом)

# Инициализация
vk_session = vk_api.VkApi(token=GROUP_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

# Состояние бота (для обработки диалога)
bot_state = {}

def get_members():
    """Получаем участников группы с обработкой ошибок"""
    try:
        members = []
        count = vk.groups.getMembers(group_id=GROUP_ID)['count']
        
        for offset in range(0, count, 1000):
            chunk = vk.groups.getMembers(
                group_id=GROUP_ID,
                offset=offset,
                count=1000
            )['items']
            members.extend(chunk)
            time.sleep(0.5)
            
        return members
    except Exception as e:
        print(f"Ошибка при получении участников: {e}")
        return []

def send_message(user_id, text):
    """Улучшенная отправка сообщений"""
    try:
        if not text or len(text) > 4096:
            print(f"Неверный текст для {user_id}")
            return False
            
        vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=int(time.time())
        )
        time.sleep(1.2)  # Важно: задержка между сообщениями
        return True
    except Exception as e:
        print(f"Ошибка отправки для {user_id}: {e}")
        return False

def handle_command(user_id, command):
    """Обработка команд"""
    global bot_state
    
    if command.lower() == 'рассылка':
        if user_id == ADMIN_ID:
            bot_state[user_id] = 'awaiting_text'
            vk.messages.send(
                user_id=user_id,
                message="Введите текст рассылки:",
                random_id=int(time.time())
            )
        else:
            vk.messages.send(
                user_id=user_id,
                message="У вас нет прав на эту команду",
                random_id=int(time.time())
            )
    elif user_id in bot_state and bot_state[user_id] == 'awaiting_text':
        # Это текст для рассылки
        text = command.strip()
        if len(text) < 2:
            vk.messages.send(
                user_id=user_id,
                message="Текст слишком короткий. Введите снова:",
                random_id=int(time.time())
            )
            return
            
        members = get_members()
        if not members:
            vk.messages.send(
                user_id=user_id,
                message="Не удалось получить список участников",
                random_id=int(time.time())
            )
            return
            
        vk.messages.send(
            user_id=user_id,
            message=f"Начинаю рассылку для {len(members)} участников...",
            random_id=int(time.time())
        )
        
        success = 0
        for member in members:
            if send_message(member, text):
                success += 1
                
        bot_state.pop(user_id, None)
        vk.messages.send(
            user_id=user_id,
            message=f"Рассылка завершена! Успешно: {success}/{len(members)}",
            random_id=int(time.time())
        )

def main():
    print("Бот запущен. Ожидаю команды...")
    
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    msg = event.object.message
                    user_id = msg['from_id']
                    text = msg.get('text', '').strip()
                    
                    if text:
                        handle_command(user_id, text)
                        
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()