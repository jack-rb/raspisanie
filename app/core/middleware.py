from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .telegram_auth import TelegramAuth
from .config import settings
import re

class TelegramWebAppMiddleware:
    def __init__(self):
        self.telegram_auth = TelegramAuth(settings.BOT_TOKEN)
        # Разрешенные домены Telegram
        self.allowed_domains = [
            'web.telegram.org',
            't.me',
            'telegram.org'
        ]
    
    async def __call__(self, request: Request, call_next):
        # Проверяем только для API endpoints
        if request.url.path.startswith('/api/'):
            return await self._check_telegram_auth(request, call_next)
        
        # Для статических файлов и главной страницы - базовая проверка
        return await self._check_basic_auth(request, call_next)
    
    async def _check_telegram_auth(self, request: Request, call_next):
        """Строгая проверка для API endpoints"""
        try:
            # Проверяем User-Agent
            user_agent = request.headers.get('user-agent', '')
            if not self.telegram_auth.is_telegram_webapp(user_agent):
                raise HTTPException(status_code=403, detail="Доступ только из Telegram WebApp")
            
            # Проверяем Referer
            referer = request.headers.get('referer', '')
            if not self._is_allowed_referer(referer):
                raise HTTPException(status_code=403, detail="Неразрешенный источник")
            
            # Проверяем initData (если есть)
            init_data = request.headers.get('x-telegram-init-data', '')
            if init_data:
                user_data = self.telegram_auth.validate_init_data(init_data)
                if not user_data:
                    raise HTTPException(status_code=403, detail="Неверная подпись Telegram")
                
                # Добавляем данные пользователя в request
                request.state.user_data = user_data
            
            response = await call_next(request)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail": "Ошибка аутентификации"}
            )
    
    async def _check_basic_auth(self, request: Request, call_next):
        """Базовая проверка для статических файлов"""
        try:
            # Проверяем Referer
            referer = request.headers.get('referer', '')
            if referer and not self._is_allowed_referer(referer):
                # Разрешаем доступ к статическим файлам без строгой проверки
                pass
            
            response = await call_next(request)
            return response
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail": "Ошибка сервера"}
            )
    
    def _is_allowed_referer(self, referer: str) -> bool:
        """Проверяет, что referer разрешен"""
        if not referer:
            return True  # Разрешаем прямые запросы
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            return any(domain in parsed.netloc for domain in self.allowed_domains)
        except:
            return False 