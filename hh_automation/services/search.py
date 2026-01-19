"""Vakansiyalarni qidirish asinxron xizmati."""

import logging
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import Page

from ..config import get_settings
from .browser import browser_manager

logger = logging.getLogger(__name__)


@dataclass
class Vacancy:
    """Vakansiya ma'lumotlar modeli."""
    title: str
    url: str
    employer: str
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "employer": self.employer,
            "description": self.description
        }


class VacancySearchService:
    """HH.ru da vakansiyalarni qidirish xizmati."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def _get_vacancy_description(self, page: Page, url: str) -> str:
        """
        Vakansiya sahifasiga o'tish va to'liq tavsifni ajratib olish.
        
        Argumentlar:
            page: Foydalanish uchun brauzer sahifasi.
            url: Vakansiya URL manzili.
            
        Qaytaradi:
            Vakansiyaning to'liq tavsif matni.
        """
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_selector("[data-qa='vacancy-description']", timeout=10000)
            
            description_el = page.locator("[data-qa='vacancy-description']")
            if await description_el.count() > 0:
                return (await description_el.inner_text()).strip()
            return ""
            
        except Exception as e:
            logger.warning(f"Vakansiya tavsifini olish muvaffaqsiz bo'ldi {url}: {e}")
            return ""

    async def _check_bot_protection(self, page: Page) -> bool:
        """Bot himoyasi ishga tushishi (kapcha) tekshirish."""
        title = await page.title()
        content = await page.content()
        return "captcha" in title.lower() or "robot" in content.lower()

    async def search(
        self,
        query: Optional[str] = None,
        page_num: int = 0
    ) -> list[dict]:
        """
        So'rovga mos keladigan vakansiyalarni qidirish.
        
        Argumentlar:
            query: So'rov matni. Sozlamalardan qiymatidan foydalaniladi.
            page_num: Paginatsiya uchun sahifa raqami (0 dan boshlanadi).
            
        Qaytaradi:
            Sarlavha, URL, ish beruvchi va tavsif bilan vakansiyalar lug'atlari ro'yxati.
            
        Istisno:
            RuntimeError: Agar bot himoyasi ishga tushsa.
            FileNotFoundError: Agar sessiya fayli topilmasa.
        """
        query = query or self._settings.default_search_text
        
        logger.info(f"Vakansiyalarni qidirish: so'rov='{query}', sahifa={page_num}")

        async with browser_manager.get_page(use_session=True) as page:
            # Qidiruv uchun URL tuzish
            url = (
                f"https://hh.ru/search/vacancy?"
                f"text={query}&area={self._settings.area_code}"
                f"&items_on_page=20&page={page_num}"
            )
            
            await page.goto(url, wait_until="domcontentloaded")
            
            if await self._check_bot_protection(page):
                raise RuntimeError("Bot himoyasi ishga tushdi (kapcha aniqlandi)")

            # Natijalaring kutilishi
            await page.wait_for_selector("[data-qa='vacancy-serp__vacancy']", timeout=10000)
            
            # Qidiruv natijalari bo'yicha vakansiyalar asosiy ma'lumotlarini to'plash
            vacancy_data: list[dict] = []
            cards = await page.locator("[data-qa='vacancy-serp__vacancy']").all()
            
            for i, card in enumerate(cards):
                try:
                    title_el = card.locator("[data-qa='serp-item__title']")
                    await title_el.wait_for(state="visible", timeout=5000)
                    
                    href = await title_el.get_attribute("href")
                    title = await title_el.inner_text()
                    
                    employer_el = card.locator("[data-qa='vacancy-serp__vacancy-employer']").first
                    employer = (
                        await employer_el.inner_text() 
                        if await employer_el.count() > 0 
                        else "Noma'lum"
                    )
                    
                    vacancy_data.append({
                        "title": title,
                        "url": href,
                        "employer": employer
                    })
                    
                except Exception as e:
                    logger.warning(f"Vakansiya kartochkasini tahlil qilish muvaffaqsiz bo'ldi {i}: {e}")
                    continue

            # Har bir vakansiya uchun to'liq tavsifni olish
            vacancies: list[dict] = []
            for data in vacancy_data:
                description = await self._get_vacancy_description(page, data["url"])
                vacancy = Vacancy(
                    title=data["title"],
                    url=data["url"],
                    employer=data["employer"],
                    description=description
                )
                vacancies.append(vacancy.to_dict())

            logger.info(f"{len(vacancies)} ta vakansiya topildi")
            return vacancies
