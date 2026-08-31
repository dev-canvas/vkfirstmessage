import os
import random
import json
import logging
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- НАСТРОЙКИ ИЗ .env ---
GROUP_ID = os.getenv("VK_GROUP_ID")
ACCESS_TOKEN = os.getenv("BOT_TOKEN")
# Формат: doc-<owner_id>_<id>, например doc-12345_67890
DOC_ATTACHMENT = os.getenv("DOC_ATTACHMENT")

if not all([GROUP_ID, ACCESS_TOKEN, DOC_ATTACHMENT]):
    raise ValueError(
        "Не заданы переменные окружения: VK_GROUP_ID, BOT_TOKEN, DOC_ATTACHMENT"
    )

GROUP_ID = int(GROUP_ID)


def create_keyboard():
    """Создаёт JSON для клавиатуры с тремя кнопками"""
    keyboard = {
        "one_time": True,  # False = кнопки остаются после нажатия
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "label": "👨‍👩‍👦 Семья"
                    },
                    "color": "primary"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "🎨 Творчество"
                    },
                    "color": "primary"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "🛍 Покупки"
                    },
                    "color": "primary"
                }
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)


def send_welcome_package(vk, user_id):
    """Отправляет приветственное сообщение с файлом и кнопками"""
    message_text = (
        "🎉 Спасибо за подписку! Мы подготовили для тебя полезный подарок — архив с фирменными стикерами. "
        "Скачивай и украшай свои сторис! 👇\n\n"
        "А пока расскажи, что тебе интереснее прямо сейчас?"
    )
    
    random_id = random.randint(-2**63, 2**63 - 1)
    keyboard_json = create_keyboard()

    # Проверка: можно ли писать пользователю
    try:
        allowed = vk.messages.isMessagesFromGroupAllowed(user_id=user_id)
        if not allowed.get("is_allowed"):
            logging.warning(f"Пользователь {user_id} запретил сообщения от группы")
            return
    except Exception as e:
        logging.error(f"Ошибка проверки разрешений: {e}")

    try:
        vk.messages.send(
            user_id=user_id,
            message=message_text,
            attachment=DOC_ATTACHMENT,  # ZIP-архив
            keyboard=keyboard_json,    # Кнопки
            random_id=random_id,
        )
        logging.info(f"Подарок и кнопки отправлены пользователю {user_id}")
    except vk_api.exceptions.ApiError as e:
        logging.error(f"API ошибка при отправке: {e}")
    except Exception as e:
        logging.error(f"Неожиданная ошибка: {e}", exc_info=True)


def handle_button_click(vk, event):
    """Обрабатывает нажатие на кнопки и отправляет ответ"""
    user_id = event.object.from_id
    text = event.object.text

    # Текст ответа для всех кнопок (можно сделать разный для каждой темы)
    response_text = (
        "Спасибо, что поделился! Для нас это очень ценно. "
        "💛"
    )

    random_id = random.randint(-2**63, 2**63 - 1)

    try:
        vk.messages.send(
            user_id=user_id,
            message=response_text,
            random_id=random_id,
        )
        logging.info(f"Ответ на кнопку отправлен пользователю {user_id}, текст: {text}")
    except vk_api.exceptions.ApiError as e:
        logging.error(f"API ошибка при ответе на кнопку: {e}")
    except Exception as e:
        logging.error(f"Неожиданная ошибка при ответе: {e}", exc_info=True)


def main():
    vk_session = vk_api.VkApi(token=ACCESS_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

    logging.info("Бот запущен и ждёт событий...")

    for event in longpoll.listen():
        # Событие: пользователь вступил в группу
        if event.type == VkBotEventType.GROUP_JOIN:
            user_id = event.object.user_id
            logging.info(f"Новый участник группы: {user_id}")
            send_welcome_package(vk, user_id)

        # Событие: пользователь отправил сообщение (сюда попадают и нажатия кнопок)
        elif event.type == VkBotEventType.MESSAGE_NEW:
            # Проверяем, что сообщение пришло в личку и не от бота
            if event.object.peer_id == event.object.from_id:
                text = event.object.text
                # Реагируем только на наши кнопки
                if text in ["👨‍👩‍👦 Семья", "🎨 Творчество", "🛍 Покупки"]:
                    handle_button_click(vk, event)


if __name__ == '__main__':
    main()
