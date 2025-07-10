import hashlib
import hmac
import json
from typing import Optional, Dict
from urllib.parse import parse_qs, urlparse

class TelegramAuth:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        # Создаем секретный ключ из токена бота
        self.secret_key = hmac.new(
            b"WebAppData",
            self.bot_token.encode(),
            hashlib.sha256
        ).digest()
    
    def validate_init_data(self, init_data: str) -> Optional[Dict]:
        """
        Проверяет подпись initData от Telegram WebApp
        """
        try:
            # Парсим параметры
            parsed = parse_qs(init_data)
            
            # Извлекаем hash
            if 'hash' not in parsed:
                return None
            received_hash = parsed['hash'][0]
            
            # Создаем строку для проверки (все параметры кроме hash)
            data_check_string = []
            for key, value in parsed.items():
                if key != 'hash':
                    data_check_string.append(f"{key}={value[0]}")
            
            # Сортируем параметры
            data_check_string.sort()
            data_check_string = '\n'.join(data_check_string)
            
            # Создаем HMAC-SHA256 подпись
            calculated_hash = hmac.new(
                self.secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Сравниваем подписи
            if calculated_hash == received_hash:
                # Возвращаем данные пользователя
                user_data = {}
                if 'user' in parsed:
                    user_data = json.loads(parsed['user'][0])
                return user_data
            
            return None
            
        except Exception as e:
            print(f"Ошибка валидации initData: {e}")
            return None
    
    def is_telegram_webapp(self, user_agent: str) -> bool:
        """
        Проверяет, что запрос пришел из Telegram WebApp
        """
        return "TelegramWebApp" in user_agent 