import asyncio
import json
import sys
import os
from typing import Optional

from ..config import get_settings
from ..services.browser import BrowserManager

async def login() -> None:
    settings = get_settings()
    settings.ensure_dirs()
    manager = BrowserManager()
    
    is_headless = settings.browser_headless
    print(f"DEBUG: is_headless={is_headless}")
    
    async with manager.get_interactive_context(headless=is_headless) as (context, page):
        # Yanada realistik User-Agent o'rnatish
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        print("\n" + "=" * 60)
        print("tashkent.hh.uz Kirish")
        print("=" * 60)

        try:
            print("tashkent.hh.uz kirish sahifasini ochish...")
            await page.goto("https://tashkent.hh.uz/login", wait_until="networkidle")
            
            if not is_headless:
                print("\n1. Ochilgan brauzer oynasida tashkent.hh.uz ga kiring")
                print("2. Siz shaxsiy profilingizni ko'rguningizcha kutib turing")
                print("3. Bu yerga qaytib Enter tugmasini bosing")
                input("\nMuvaffaqiyatli kirdingizdan so'ng Enter tugmasini bosing...")
            else:
                print("\n[DOCKER REJIMI] Avtomatlashtirilgan kirishan boshlanmoqda...")
                
                # 1-qadam: Akkaunt turi \"Qidiruvchi\" (applicant) tanlanganligigini tekshiring
                try:
                    print("'Ariza beruvchi' akkaunt turi tanlanganligigini tekshiryapman...")
                    applicant_radio = await page.wait_for_selector(
                        'input[data-qa="account-type-card-APPLICANT"]', 
                        timeout=5000
                    )
                    
                    is_checked = await applicant_radio.is_checked()
                    if not is_checked:
                        await applicant_radio.check()
                        print("✓ 'Ariza beruvchi' akkaunt turi tanlandi")
                    else:
                        print("✓ 'Ariza beruvchi' akkaunt turi allaqachon tanlangan")
                    
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Ogohlantiruv: Ariza beruvchi radio tugmasini tanlay olmadim: {e}")
                
                # 2-qadam: Kirish formiga o'tish uchun "Kirish" tugmasini bosing
                try:
                    print("'Kirish' tugmasini bosamiz...")
                    submit_button = await page.wait_for_selector(
                        'button[data-qa="submit-button"]',
                        timeout=5000
                    )
                    await submit_button.click()
                    print("✓ 'Kirish' tugmasi bosildi")
                    
                    # Kirish formasi bilan sahifaning yuklanishini kutamiz
                    await asyncio.sleep(3)
                except Exception as e:
                    raise Exception(f"Kirish tugmasini bosa olmadim: {e}")
                
                # 3-qadam: Email/telefon kiritish maydonini qidiramiz
                user_input = input("\ntashkent.hh.uz Emailingizni yoki Telefonni kiriting: ").strip()
                
                # DEBUG: HTML sahifasini analiz uchun saqlash
                html_content = await page.content()
                with open("data/login_form_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("DEBUG: HTML kirish formasi data/login_form_page.html fayliga saqlandi")
                
                # Bu telefon yoki email ekanligini aniqlash
                is_phone = user_input.startswith('+') or user_input.isdigit()
                
                if is_phone:
                    # Raqamning boshidan +998 ni olib tashlash
                    phone_number = user_input.replace('+', '').replace(' ', '').replace('-', '')
                    if phone_number.startswith('998'):
                        phone_number = phone_number[3:]  # Birinchi '998' raqamini olib tashlash
                    
                    print(f"Telefon raqami kiritilmoqda (mamlakat kodisiz): {phone_number}")
                    
                    # Telefon raqami kiritish maydonini qidirish (mamlakat kodi bo'lmasdan)
                    phone_input_selector = 'input[data-qa="magritte-phone-input-national-number-input"]'
                    try:
                        phone_field = await page.wait_for_selector(phone_input_selector, timeout=5000)
                        await phone_field.fill(phone_number)
                        print("✓ Telefon raqami maydoni to'ldirildi")
                    except Exception as e:
                        raise Exception(f"Telefon raqamini kiritish maydoni topilmadi: {e}")
                        
                else:
                    # Bu email, "Pochta" varaqasiga o'tish kerak
                    print("Email varaqasiga o'tilmoqda...")
                    try:
                        email_tab = await page.wait_for_selector('input[data-qa="credential-type-EMAIL"]', timeout=5000)
                        await email_tab.click()
                        await asyncio.sleep(1)
                        print("✓ Email varaqasiga o'tildi")
                    except Exception as e:
                        print(f"Ogohlantiruv: Email varaqasiga o'ta olmadim: {e}")
                    
                    # Email kiritish maydonini qidirish
                    email_selectors = [
                        'input[type="email"]',
                        'input[name="login"]',
                        'input[data-qa*="email"]',
                    ]
                    
                    email_field = None
                    for selector in email_selectors:
                        try:
                            email_field = await page.wait_for_selector(selector, timeout=3000)
                            if email_field and await email_field.is_visible():
                                await email_field.fill(user_input)
                                print("✓ Email maydoni to'ldirildi")
                                break
                        except:
                            continue
                    
                    print("⚠️  Email maydoniga kiritildi")
                    raise Exception("Email kiritish maydonini topa olmadim")
                
                # "Keyingi" tugmasini bosing
                await page.click('button[data-qa="submit-button"]')
                print("✓ 'Keyingi' tugmasi bosildi")
                
                # Keyingi sahifa yoki OTP xabarini kutamiz
                print("OTP yoki keyingi qadam kutilmoqda...")
                await asyncio.sleep(3)
                
                # Debuging uchun skrinshot saqlash
                await page.screenshot(path="data/after_submit.png")
                print("DEBUG: Skrinshot data/after_submit.png ga saqlandi")
                
                # Kod maydonini kutamiz - turli selektorlarni sinab ko'rish
                print("OTP kod so'rovini tekshiryapman...")
                
                otp_selectors = [
                    'input[data-qa="otp-code-input"]',
                    'input[inputmode="numeric"]',
                    'input[type="text"][inputmode="numeric"]',
                    'input[name="code"]',
                    'input[placeholder*="код"]',
                ]
                
                otp_field = None
                for selector in otp_selectors:
                    try:
                        otp_field = await page.wait_for_selector(selector, timeout=5000)
                        if otp_field and await otp_field.is_visible():
                            print(f"✓ OTP maydoni topildi selector bilan: {selector}")
                            break
                    except:
                        continue
                
                if otp_field:
                    otp_code = input("\n🔐 Sizga yuborilgan OTP kodni kiriting: ").strip()
                    await otp_field.fill(otp_code)
                    print("✓ OTP kod kiritildi")
                    
                    # OTP tasdiqlash tugmasini qidirish
                    try:
                        # Tasdiqlash tugmasini kutamiz
                        await asyncio.sleep(1)
                        confirm_button_selectors = [
                            'button[data-qa="submit-button"]',
                            'button[type="submit"]',
                        ]
                        
                        for btn_selector in confirm_button_selectors:
                            try:
                                confirm_btn = await page.wait_for_selector(btn_selector, timeout=3000)
                                if confirm_btn and await confirm_btn.is_visible():
                                    await confirm_btn.click()
                                    print("✓ OTP tasdiqlash tugmasi bosildi")
                                    break
                            except:
                                continue
                    except Exception as e:
                        print(f"Eslatma: OTP tasdiqlash tugmasini topa olmadim/bosa olmadim: {e}")
                    
                    # Kod kiritilgandan so'ng HH odatda o'z-o'zidan yo'naltiradi, kutamiz
                    print("Tasdiqlanmoqda... iltimos kutib turing.")
                    await asyncio.sleep(5)
                else:
                    print("⚠️  OTP maydoni aniqlandi. Ehtimoliy sabablar:")
                    print("   - Siz allaqachon tizimga kirgansiz")
                    print("   - Sahifa parol o'rniga OTP talab etishi mumkin")
                    print("   - Xato ro'y berdi")
                    print("   Nima bo'lganini ko'rish uchun data/after_submit.png ni tekshiring")

                cookies = await context.cookies()
                if not any(c['name'] == 'hhtoken' for c in cookies):
                    print("⚠️  Ogohlantiruv: 'hhtoken' cookies da topilmadi. Kirish muvaffaqsiz bo'lishi mumkin.")
                else:
                    print("✓ Muvaffaqiyatli autentifikatsiya!")

        except Exception as e:
            print(f"\n[XATO] {e}")
            await page.screenshot(path="data/error_login.png")
            print("Skrinshot data/error_login.png ga saqlandi. Nima bo'lganini ko'rish uchun uni tekshiring.")
            return

        # Sessiyani saqlash
        await context.storage_state(path=str(settings.session_file))
        print(f"\n✓ Sessiya saqlandi: {settings.session_file}")

def main() -> None:
    asyncio.run(login())

if __name__ == "__main__":
    main()
