import requests
import os
import sys
from datetime import datetime
import pytz

def get_weather():
    cities = {
        "Pavia": {"lat": 45.192, "lon": 9.159},
        "Berlino": {"lat": 52.520, "lon": 13.405}
    }
    messages = ["Buongiorno Anna e Francesco! Ecco il meteo di oggi:"]

    for name, coord in cities.items():
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={coord['lat']}&longitude={coord['lon']}"
            f"&current_weather=true&timezone=Europe%2FRome"
        )
        try:
            r = requests.get(url, timeout=10).json()
            if "current_weather" not in r:
                messages.append(f" - {name}: errore dati")
                continue

            data = r["current_weather"]
            temp = round(data["temperature"])
            feels = temp
            wmo = data["weathercode"]

            if wmo == 0:
                desc = "cielo sereno"
            elif wmo in [1,2,3]:
                desc = "poco nuvoloso" if wmo < 3 else "nuvoloso"
            elif wmo in [45,48]:
                desc = "nebbia"
            elif 51 <= wmo <= 67:
                desc = "pioggia"
            elif 71 <= wmo <= 79:
                desc = "neve"
            elif wmo >= 80:
                desc = "temporali / rovesci"
            else:
                desc = "variabile"

            emoji = "☀️" if data.get("is_day", 1) else "🌙"
            if "pioggia" in desc: emoji = "🌧️"
            elif "neve" in desc: emoji = "❄️"
            elif "nebbia" in desc: emoji = "🌫️"
            elif "temporali" in desc: emoji = "⛈️"

            line = f"{emoji} {name}: {temp}°C (percepiti {feels}°C) - {desc}"
            messages.append(line)
        except Exception:
            messages.append(f" - {name}: problema connessione")

    messages.append("Buona giornata!")
    return "\n".join(messages)

def send_telegram(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    if not token or not chat_id:
        print("Mancano token o chat_id")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        response = requests.post(url, json=payload, timeout=10)
        print("Status:", response.status_code)
        print("Risposta Telegram:", response.text)
        if response.status_code == 200 and response.json().get("ok") == True:
            print("Inviato correttamente")
            return True
        else:
            print("Problema invio:", response.text)
            return False
    except Exception as e:
        print("Eccezione:", str(e))
        return False

if __name__ == "__main__":
    now_rome = datetime.now(pytz.timezone("Europe/Rome"))
    force = len(sys.argv) > 1 and sys.argv[1].lower() in ["force", "test"]
    is_time = (now_rome.hour == 6 and 28 <= now_rome.minute <= 45)

    if force or is_time:
        print(f"Invio attivato ({now_rome.strftime('%H:%M')})")
        msg = get_weather()
        success = send_telegram(msg)
        print("Esito:", "OK" if success else "FALLITO")
        if not success:
            sys.exit(1)
    else:
        print("Non orario di invio")
