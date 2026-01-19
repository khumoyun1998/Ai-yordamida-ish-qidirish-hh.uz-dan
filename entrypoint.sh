#!/bin/bash

# Sessiya fayli mavjudligini tekshiramiz
if [ ! -f "/app/data/hh_session.json" ]; then
    echo "--------------------------------------------------------"
    echo "OGOHLANTIRISH: Sessiya fayli topilmadi!"
    echo "Avtomatlashtirish uchun hh.uz ga bir marta kirish kerak."
    echo "Iltimos, terminalda yangi oynada quyidagi buyruqni bajarang:"
    echo "docker exec -it hh-automation python -m hh_automation.cli.login"
    echo "--------------------------------------------------------"
else
    echo "Sessiya topildi. Server ishga tushmoqda..."
fi

# Asosiy server jarayonini ishga tushiramiz
exec python -m hh_automation.server
