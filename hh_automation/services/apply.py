"""Vakansiyalarga javob berish uchun asinxron xizmat."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from playwright.async_api import Page

from .browser import browser_manager

logger = logging.getLogger(__name__)


class ApplyStatus(str, Enum):
    """Statusi kodlari"""
    SUCCESS = "success"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class ApplyResult:
    """Vakansiyaga javob berish urinishining natijasi."""
    status: ApplyStatus
    message: str

    def to_dict(self) -> dict:
        return {"status": self.status.value, "message": self.message}


class VacancyApplyService:
    """HH.ru da vakansiyalarga javob berish xizmati."""

    async def _check_bot_protection(self, page: Page) -> bool:
        """Bot himoyasi ishga tushishi (kapcha) tekshirish."""
        title = await page.title()
        content = await page.content()
        return "captcha" in title.lower() or "robot" in content.lower()

    async def _check_already_applied(self, page: Page) -> bool:
        """Ushbu vakansiyaga javob berilganligini tekshirish."""
        locator = page.locator("text=Siz javob berdingiz")
        return await locator.count() > 0

    async def _fill_cover_letter_modal(
        self,
        page: Page,
        message: str
    ) -> Optional[ApplyResult]:
        """
        Modal oynasida qo'llash xatini to'ldirish va yuborish.
        
        Qaytaradi:
            Muvaffaqiyatlilik holatida ApplyResult, agar modal bilan o'zaro aloqa muvaffaqsiz bo'lsa None.
        """
        try:
            logger.debug("Qo'llash modali kutilmoqda...")
            await page.wait_for_selector("[data-qa='vacancy-response-popup']", timeout=5000)
            await page.wait_for_timeout(1000)
            
            letter_area = page.locator(
                "textarea[data-qa='vacancy-response-popup-form-letter-input']"
            )
            if await letter_area.count() > 0:
                logger.debug(f"Qo'llash xatini to'ldirish ({len(message)} harf)")
                await letter_area.fill(message)
            else:
                logger.warning("Modal oynasida qo'llash xatining maydoni topilmadi")
            
            submit_btn = page.locator("button[data-qa='vacancy-response-submit-popup']")
            if await submit_btn.count() > 0:
                await submit_btn.click()
                await page.wait_for_timeout(3000)
                return ApplyResult(ApplyStatus.SUCCESS, "Qo'llash xati bilan javob berildi")
            else:
                return ApplyResult(ApplyStatus.ERROR, "Yuborish tugmasi topilmadi")
                
        except Exception as e:
            logger.error(f"Modal bilan ishlash muvaffaqsiz bo'ldi: {e}")
            return None

    async def _try_cover_letter_link(
        self,
        page: Page,
        message: str
    ) -> Optional[ApplyResult]:
        """'Qo'llash xatini yozish' havolasi orqali javob berish urinishi."""
        cover_letter_link = page.locator("a:has-text('Написать сопроводительное')")
        
        if await cover_letter_link.count() > 0 and message:
            logger.debug("'Qo'llash xati yozish' havolasi topildi, bosish...")
            await cover_letter_link.first.click()
            result = await self._fill_cover_letter_modal(page, message)
            if result:
                return result
        
        return None

    async def _try_dropdown_apply(
        self,
        page: Page,
        message: str
    ) -> Optional[ApplyResult]:
        """Qo'llash xatiga ega belgili menyu orqali javob berish urinishi."""
        dropdown_arrow = page.locator(
            "[data-qa='vacancy-response-link-top'] + button, "
            "[data-qa='vacancy-response-link-bottom'] + button"
        )
        
        if await dropdown_arrow.count() > 0 and message:
            logger.debug("Belgili menyu topildi, kengaytirish...")
            await dropdown_arrow.first.click()
            await page.wait_for_timeout(500)
            
            with_letter_option = page.locator("text=Kuzatuv xati bilan")
            if await with_letter_option.count() > 0:
                await with_letter_option.first.click()
                result = await self._fill_cover_letter_modal(page, message)
                if result:
                    return result
        
        return None

    async def _try_post_apply_letter(
        self,
        page: Page,
        message: str
    ) -> Optional[ApplyResult]:
        """Javob berish o'tkazilganidan so'ng qo'llash xatini to'ldirish urinishi."""
        resume_delivered = page.locator("text=Rezyume yetkazildi")
        
        if await resume_delivered.count() > 0 or await page.locator("textarea").count() > 0:
            logger.debug("Javob berish utkazilgan o'tkazilgan ekran topildi")
            
            letter_area = page.locator("textarea")
            if await letter_area.count() > 0 and message:
                await letter_area.first.fill(message)
                
                submit_btn = page.locator("button:has-text('Yuborish')")
                if await submit_btn.count() > 0:
                    await submit_btn.first.click()
                    await page.wait_for_timeout(2000)
                    return ApplyResult(ApplyStatus.SUCCESS, "Javob berish o'tkazilganidan so'ng qo'llash xati bilan javob berildi")
        
        return None

    async def _check_application_success(self, page: Page) -> bool:
        """Javob berish muvaffaqiyatli yuborilganligini tekshirish."""
        success_texts = [
            "text=Javob topshirildi",
            "text=Siz javob berdingiz",
            "text=Rezyume yetkazildi"
        ]
        for selector in success_texts:
            if await page.locator(selector).count() > 0:
                return True
        return False

    async def apply(self, url: str, message: str = "") -> dict:
        """
        Vakansiyaga ixtiyoriy qo'llash xati bilan javob bering.
        
        Argumentlar:
            url: Vakansiya URL manzili.
            message: Ixtiyoriy qo'llash xatining matni.
            
        Qaytaradi:
            Holat va xabar bilan lug'at.
        """
        logger.info(f"Quyidagiga javob berilmoqda: {url}")
        if message:
            logger.debug(f"Qo'llash xati: {len(message)} harf")

        try:
            async with browser_manager.get_page(use_session=True) as page:
                # Vakansiyaga o'tish
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception as e:
                    logger.warning(f"Navigatsiya timeout: {e}")
                    # Baraye ham davom ettiring, sahifa etarli darajada yuklanishi mumkin

                # Bot himoyasi tekshirish
                if await self._check_bot_protection(page):
                    return ApplyResult(
                        ApplyStatus.ERROR,
                        "Bot himoyasi ishga tushdi (kapcha)"
                    ).to_dict()

                # Oldindan javob berilganligini tekshirish
                if await self._check_already_applied(page):
                    return ApplyResult(ApplyStatus.SKIPPED, "Allaqachon javob berilgan").to_dict()

                # Strategiya 1: Qo'llash xati havolasi orqali urinish
                result = await self._try_cover_letter_link(page, message)
                if result:
                    return result.to_dict()

                # Javob berish tugmasini qidirish
                apply_btn = page.locator("[data-qa='vacancy-response-link-top']")
                if await apply_btn.count() == 0:
                    apply_btn = page.locator("[data-qa='vacancy-response-link-bottom']")

                if await apply_btn.count() == 0:
                    return ApplyResult(
                        ApplyStatus.ERROR,
                        "Javob berish tugmasi topilmadi"
                    ).to_dict()

                # Strategiya 2: Belgili ro'yxat orqali qo'llash xati bilan urinish
                result = await self._try_dropdown_apply(page, message)
                if result:
                    return result.to_dict()

                # Strategiya 3: Standart javob berish tugmasi
                logger.debug("Standart javob berish tugmasini bosamiz...")
                await apply_btn.first.click()
                await page.wait_for_timeout(2000)

                # Strategiya 4: Javob berish o'tkazilgandan so'ng qo'llash xati
                result = await self._try_post_apply_letter(page, message)
                if result:
                    return result.to_dict()

                # Javob berish muvaffaqiyatligini tekshirish
                if await self._check_application_success(page):
                    return ApplyResult(ApplyStatus.SUCCESS, "Muvaffaqiyatli javob berildi").to_dict()
                else:
                    return ApplyResult(
                        ApplyStatus.SUCCESS,
                        "Javob berildi (holati aniq emas)"
                    ).to_dict()

        except FileNotFoundError as e:
            return ApplyResult(ApplyStatus.ERROR, str(e)).to_dict()
        except Exception as e:
            logger.error(f"Qo'llash muvaffaqsiz bo'ldi: {e}", exc_info=True)
            return ApplyResult(ApplyStatus.ERROR, str(e)).to_dict()
