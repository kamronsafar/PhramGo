# PhramGo 🏥💊 — Telegram Assistant for Medical Help

**PhramGo** is an intelligent Telegram bot designed to help users in Uzbekistan quickly find nearby pharmacies, clinics, emergency contact info, and even receive AI-powered diagnostics and drug search assistance — all in one seamless experience.

---

## 🔧 Features

- 📍 **Nearby Clinics & Pharmacies**  
  Share your location and instantly discover clinics and pharmacies within a defined radius (1–2 km).

- 🤖 **AI Diagnostic Assistant**  
  Type in your symptoms and get intelligent responses powered by OpenAI GPT to understand possible illnesses and treatments.

- 🔍 **Smart Drug Search**  
  Search for medications by name, get pharmacy details, and location maps. The bot uses fuzzy matching and multilingual support.

- 🚨 **Emergency Mode**  
  One-tap access to Uzbekistan’s emergency numbers and assistance options. It also allows fast location sharing for emergency services.

---

## 💡 How It Works

1. **User interacts with the bot** using a menu (geolocation, drug search, diagnostics, emergency).
2. **Location-based data** is used to calculate proximity using the Haversine formula.
3. **Drug data** is fetched from a local SQLite database.
4. **Diagnostic responses** are handled via OpenAI’s GPT-4 model.
5. **Multilingual drug search** is handled via automatic translation using `deep_translator`.

---

## 📦 Technologies Used

- [Python 3.10+](https://www.python.org/)
- [Aiogram](https://docs.aiogram.dev/) – Telegram bot framework
- [OpenAI GPT-4](https://openai.com/)
- [SQLite3](https://www.sqlite.org/)
- [Deep Translator](https://pypi.org/project/deep-translator/) – for language translation
- [Difflib](https://docs.python.org/3/library/difflib.html) – for fuzzy matching
- [Google Maps](https://www.google.com/maps) – for location preview

---

## 🗄️ Database Schema

- **clinics** – Stores clinic info (`name`, `lat`, `lon`, `phone`, `address`)
- **pharmacy** – Stores pharmacy info
- **drugs** – Stores drug-to-pharmacy relations
- **user_data** – Saves user location for tracking nearby services

---

## ⚙️ Setup Instructions

1. **Clone the repo**
   ```bash
   git clone https://github.com/kamronsafar/PhramGo
   cd PhramGo
   ```
2   
Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

3
Set up environment variables in config.py:
```python
BOT_TOKEN = 'your_telegram_bot_token'
OPENAI_API_KEY = 'your_openai_api_key'
```

4
Ensure your SQLite DB (base.db) is prepared
Include tables: clinics, pharmacy, drugs, user_data.

5
Run the bot
```bash
python bot.py
```
