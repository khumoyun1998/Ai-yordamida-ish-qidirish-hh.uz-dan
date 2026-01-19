# Uzbekiston uchun sozlanadi. 

# HH.ru Avtomatlashtirish

Python + n8n + Google Gemini AI orqali HH.ru da vakansiyalarni qidirish va ariza topshirishning asinxron avtomatizatsiyasi.



## v2.0 xususiyatlari

- ⚡ **Async FastAPI** 
- 🎭 **Async Playwright** 
- 📖 **Swagger UI** — `/docs` sayfasida avtomatik API hujjatlar

## O'rnatish

### 1. Virtual muhit yaratish

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# yoki
.venv\Scripts\activate     # Windows
```

### 2. Bog'liq paketlarni o'rnatish

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Muhitni sozlash

Proyekt ildizida `.env` fayli yarating:

```env
# Sessiya saqlash uchun katalog yo'li
N8N_FILES_DIR=/Users/your_username/.n8n-files

# Server sozlamalari
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

# Qidiruv sozlamalari
#DEFAULT_SEARCH_TEXT=Frontend
AREA_CODE=97

# Brauzer sozlamalari (ixtiyoriy)
BROWSER_HEADLESS=true
BROWSER_SLOW_MO=0
PAGE_TIMEOUT=30000
```

**Muhim:** `/Users/your_username/.n8n-files` ni haqiqiy yo'l bilan almashtiring.

## Ishga tushirish

### Variyant 1: Docker orqali ishga tushirish (tavsiya etiladi)

Docker sizning tizimingizda Python va bog'liq paketlarni o'rnatmasdan ilova ishga tushirish imkonini beradi.

#### Talablar

- Docker Desktop (Windows/Mac uchun) yoki Docker Engine (Linux uchun)
- docker-compose (odatda Docker Desktop bilan keladi)

#### 1. Konteynerlarni yig'ish va ishga tushirish

Proyekt ildiz katalogida bajarang:

```bash
docker-compose up -d
```

Bu buyruq:
- Docker rasmni yig'adi
- Ikki konteyner ishga tushiradi: `hh-automation` (API serveri) va `n8n` (workflow tizimi)
- HH Automation serveri `http://localhost:8000` manzilida mavjud bo'ladi
- n8n `http://localhost:5678` manzilida mavjud bo'ladi

#### 2. HH.ru da avtorizatsiya

Konteynerlarni ishga tushirgandan keyin HH.ru da **bir marta** avtorizatsiya qilish kerak:

```bash
docker exec -it hh-automation python -m hh_automation.cli.login
```

Brauzer ochiladi. HH.ru hisobiga kiring, keyin terminaldagi Enter tugmasini bosing. Sessiya `./data/hh_session.json` katalogida saqlanadi.

#### 3. n8n ni sozlash

1. Brauzerda `http://localhost:5678` ni oching
2. n8n hisobini yarating (birinchi launch qilinganda)
3. `HH.ru Flow (With AI and Pagination).json` fayldan workflow import qiling
4. n8n ga Google Gemini API credentials qo'shing (Settings → Credentials)
5. Workflowni ishga tushiring

P.S. Agar workflow server bilan ishga tushmasa, nodes da server manzilini `http://hh-automation:8000` ga almashtiring

#### 4. Konteynerlarni boshqarish

**Loglarni ko'rish:**
```bash
# Barcha servislar
docker-compose logs -f

# Faqat HH Automation
docker-compose logs -f hh-automation

# Faqat n8n
docker-compose logs -f n8n
```

**To'xtash:**
```bash
docker-compose down
```

**Kod o'zgartirilgandan keyin qayta ishga tushirish:**
```bash
docker-compose restart hh-automation
```

**Rasmni to'liq qayta yig'ish:**
```bash
docker-compose up -d --build
```

#### 5. Ishchi holini tekshirish

```bash
# API tekshirish
curl http://localhost:8000/health

# Swagger hujjatlar
# Brauzerda: http://localhost:8000/docs
```

### Variyant 2: Mahalliy ishga tushirish (Dockerxsiz)

#### 1. HH.ru da avtorizatsiya

Birinchi foydalanishdan oldin sessiyani saqlang:

```bash
python -m hh_automation.cli.login
```

Brauzer ochiladi. HH.ru hisobiga kiring, keyin Enter tugmasini bosing.

#### 2. Serverni ishga tushirish

```bash
python -m hh_automation.server
```

Server `http://127.0.0.1:8000` da ishga tushadi.

#### 3. n8n ni sozlash

1. `HH.ru Flow (With AI and Pagination).json` fayldan workflow import qiling
2. n8n ga Google Gemini API credentials qo'shing (Settings → Credentials)
3. Workflowni ishga tushiring

## API Endpoints

### GET /search

Vakansiyalarni qidirish.

**Parametrlar:**
- `text` — qidiruv so'rovi (standart: "Frontend")
- `page` — sahifa raqami, 0 dan boshlanadi (standart: 0)

**Misol:**
```bash
curl "http://127.0.0.1:8000/search?text=Python&page=0"
```

### POST /apply

Vakansiyaga javob.

**Body:**
```json
{
  "url": "https://hh.ru/vacancy/123456",
  "message": "Soprovoditel'noe pis'mo matni"
}
```

**Misol:**
```bash
curl -X POST http://127.0.0.1:8000/apply \
  -H "Content-Type: application/json" \
  -d '{"url": "https://hh.ru/vacancy/123456", "message": "Assalоmu alaykum..."}'
```

### GET /health

Serverni holati tekshirish.

**Misol:**
```bash
curl http://127.0.0.1:8000/health
```

### GET /docs

Interaktiv API hujjati bilan Swagger UI.

## Proyekt tuzilishi

```
.
├── hh_automation/
│   ├── __init__.py
│   ├── config.py           # Markaziy konfiguratsiya
│   ├── server.py           # FastAPI serveri
│   ├── services/
│   │   ├── __init__.py
│   │   ├── browser.py      # Async Playwright menejeri
│   │   ├── search.py       # Vakansiya qidiruv xizmati
│   │   └── apply.py        # Javob berish xizmati
│   └── cli/
│       ├── __init__.py
│       └── login.py        # Avtorizatsiya uchun CLI
├── requirements.txt
├── .env                    # Konfiguratsiya (qo'lda yarating)
└── HH.ru Flow (With AI and Pagination).json  # n8n workflow
```

## v1.0 dan migratsiya

Eski fayllar (`hh_server.py`, `hh_login.py`, `search_vacancies.py`, `apply_vacancy.py`) 
yangi versiyani muvaffaqiyatli sinab o'tkaganidan keyin o'chirilishi mumkin.

**API o'zgarishlari:**
- Endpointlar shu bilan qoldi (`/search`, `/apply`)
- `/health` endpointi qo'shildi
- `/docs` da Swagger UI qo'shildi

## Muammolarni hal qilish

### Session fayli topilmadi

```bash
python -m hh_automation.cli.login
```

### Playwright brauzeri topilmadi

```bash
playwright install chromium
```

### ModuleNotFoundError

Virtual muhit faollashtirilganligini tekshiring:
```bash
source .venv/bin/activate
```

### pydantic-settings import xatosi

```bash
pip install pydantic-settings
```

## Cheklovlar

- HH.ru dan rate limiting bilan ishlash yo'q
- Sessiyani vaqti-vaqti bilan yangilash kerak
- Captcha avtomatik ravishda qayta ishlanmaydi

## Google Gemini API

API kalitini oling: [Google AI Studio](https://makersuite.google.com/app/apikey)

Bepul tier: 60 so'rov/minut (avtomatizatsiya uchun etarli).

## Tavsiyalar

1. Bir yuklama uchun 3-5 sahifadan ko'p bo'lmaydi (60-100 vakansiya)
2. Javoblar o'rtasida kechikish ishlating (minimum 5 soniya)
3. Sessiyani haftada bir marta yangilang: `python -m hh_automation.cli.login`
4. HH.ru shaxsiy kabinet idan javob statistikasini monitor qiling
