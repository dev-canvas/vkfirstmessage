import os
import random
import logging
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GROUP_ID = os.getenv("VK_GROUP_ID")
ACCESS_TOKEN = os.getenv("BOT_TOKEN")
LINK_TO_SEND = os.getenv("VK_LINK_TO_SEND")

if not all([GROUP_ID, ACCESS_TOKEN, LINK_TO_SEND]):
    raise ValueError(
        "Одна или несколько переменных окружения не заданы: "
        "VK_GROUP_ID, VK_ACCESS_TOKEN, VK_LINK_TO_SEND"
    )

GROUP_ID = int(GROUP_ID)

def send_welcome_link(vk, user_id, link):
	
	message = f'Спасибо за подписку! Забирай быстрее стикеры по ссылке: {link}'
    random_id = random.randint(-2**63, 2**63 - 1)  # уникальный ID для каждого сообщения

    # Опционально: сначала проверить, можно ли писать
    try:
        allowed = vk.messages.isMessagesFromGroupAllowed(user_id=user_id)
        if not allowed.get("is_allowed"):
            logging.warning(f"Пользователь {user_id} запретил сообщения от группы")
            return
    except Exception as e:
        logging.error(f"Ошибка проверки разрешений для пользователя {user_id}: {e}")
        # Можно всё равно попробовать отправить или пропустить — на твой выбор

    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random_id,
        )
        logging.info(f"Сообщение отправлено пользователю {user_id}")
    except vk_api.exceptions.ApiError as e:
        logging.error(f"API ошибка при отправке пользователю {user_id}: {e}")
    except Exception as e:
        logging.error(f"Неожиданная ошибка отправки пользователю {user_id}: {e}", exc_info=True)

def main():
    vk_session = vk_api.VkApi(token=ACCESS_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

    logging.info("Бот запущен и ждёт событий вступления в группу...")

    for event in longpoll.listen():
        if event.type == VkBotEventType.GROUP_JOIN:
            user_id = event.object.user_id
            logging.info(f"Новый участник группы: {user_id}")
            send_welcome_link(vk, user_id, LINK_TO_SEND)

if __name__ == '__main__':
    main()
