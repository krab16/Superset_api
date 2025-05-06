# 🚀 Superset API Export & Import Tool

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Superset](https://img.shields.io/badge/Apache-Superset-red)

Инструмент для безопасного экспорта и импорта дашбордов Apache Superset с расширенными возможностями управления сессиями.

## 📌 Основные возможности

### 📤 Экспорт дашбордов
- **Полный экспорт**  
  ```bash
  python export_dash_v4.0.py -s all
→ Сохраняет все дашборды в отдельных архивах

Выборочный экспорт

bash
python export_dash_v4.0.py -n <ID_DASHBOARD>
→ Экспортирует конкретный дашборд по его ID

📥 Импорт дашбордов
Единая сессия для всех операций

Поддержка параметра verify=False для тестовых сред

Сохранение целостности данных

⚙️ Установка и использование
Клонируйте репозиторий:

bash
git clone https://github.com/your-repo/Superset-API-Tool.git
Установите зависимости:

bash
pip install -r requirements.txt
Запустите нужный скрипт с параметрами:

Параметр	Описание	Пример
-s all	Экспорт всех дашбордов	export_dash.py -s all
-n X	Экспорт дашборда с ID = X	export_dash.py -n 42
⚠️ Важная информация о безопасности
Использование verify=False отключает проверку SSL-сертификатов, что может представлять риск. Рекомендуем:

✔ Для тестовых сред:

Использовать самоподписанные сертификаты

Ограничить доступ к инструменту

✔ Для production-сред:

Всегда включать SSL-проверку

Использовать валидные сертификаты

Настроить параметры в config.ini:

ini
[security]
verify_ssl = true
cert_path = /path/to/cert.pem
📂 Структура проекта
Superset-API-Tool/
├── docs/                 # Документация
├── examples/             # Примеры конфигов
├── scripts/              # Основные скрипты
│   ├── export_dash.py    # v4.0 с новыми параметрами
│   └── import_dash.py    # Импорт с единой сессией
└── requirements.txt      # Зависимости
🤝 Как внести свой вклад
Создайте issue с описанием улучшения

Форкните репозиторий

Создайте feature-ветку

Отправьте Pull Request

📬 Контакты
Для вопросов и предложений:

Открыть Issue

Email: your@email.com

<div align="center"> <sub>Разработано с ❤️ для сообщества Apache Superset | 2023</sub> </div> ```
