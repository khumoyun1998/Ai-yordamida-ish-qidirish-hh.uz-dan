"""Playwright brauzer asinkron boshqaruvi"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from ..config import get_settings

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Playwright brauzeri hayot tsiklini boshqaradi.
    """

    def __init__(self) -> None:
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()
        self._settings = get_settings()

    async def start(self) -> None:
        """Playwright va brauzer ishga tushirishini boshlash."""
        async with self._lock:
            if self._playwright is None:
                logger.info("Playwright ishga tushmoqda...")
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self._settings.browser_headless,
                    slow_mo=self._settings.browser_slow_mo
                )
                logger.info("Brauzer muvaffaqiyatli ishga tushdi")

    async def stop(self) -> None:
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            logger.info("Brauzer to'xtatildi")

    def _validate_session(self) -> None:
        """Sessiya faylining mavjudligi va to'g'riligi tekshiruvi."""
        if not self._settings.session_file.exists():
            raise FileNotFoundError(
                f"Session file not found: {self._settings.session_file}. "
                "Run 'python -m hh_automation.cli.login' first."
            )

    @asynccontextmanager
    async def get_page(self, use_session: bool = True) -> AsyncGenerator[Page, None]:
        """
        Shaxsiy sessiya holatiga ega brauzer sahifasini olish.
        
        Argumentlar:
            use_session: Saqlangan autentifikatsiya holatini yuklash kerakmi.
            
        Qaytaradi:
            Foydalanishga tayyorlanmish sozlanmış brauzer sahifasi.
        """
        if not self._browser:
            await self.start()

        context: Optional[BrowserContext] = None
        try:
            if use_session:
                self._validate_session()
                context = await self._browser.new_context(
                    storage_state=str(self._settings.session_file)
                )
            else:
                context = await self._browser.new_context()

            page = await context.new_page()
            page.set_default_timeout(self._settings.page_timeout)
            
            yield page
            
        finally:
            if context:
                await context.close()

    @asynccontextmanager
    async def get_interactive_context(self, headless: Optional[bool] = None) -> AsyncGenerator[tuple[BrowserContext, Page], None]:
        """
        Manual operatsiyalar uchun interaktiv brauzer kontekstini olish (masalan, kirish).
        
        Qaytaradi:
            Kortej (context, page)
        """
        if headless is None:
            headless = self._settings.browser_headless

        # Interaktiv foydalanish uchun brauzer ishga tushirish
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                yield context, page
            finally:
                await browser.close()


# Brauzer menejer global namunasi
browser_manager = BrowserManager()
