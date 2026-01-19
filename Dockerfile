FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

COPY requirements.txt .

# Python paketlarini o'rnatamiz
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

# Proyekt manba kodini ko'chiramiz
COPY . .

# Ishga tushirish skriptini faollashtirish
RUN chmod +x /app/entrypoint.sh

# O'zgaruvchanlarni o'rnatamiz
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000
ENV N8N_FILES_DIR=/app/data
ENV BROWSER_HEADLESS=true
ENV PYTHONPATH=/app

# Ma'lumotlar uchun katalogni yaratamiz
RUN mkdir -p /app/data

# Portni ochib qo'yamiz
EXPOSE 8000

# Kirish skriptini foydalaning
ENTRYPOINT ["/app/entrypoint.sh"]
