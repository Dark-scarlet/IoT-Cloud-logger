import time
import requests
import geocoder
from twilio.rest import Client

# -------------------
# CONFIGURATION
# -------------------
OPENWEATHER_API_KEY = "REMOVED"
THINGSPEAK_API_KEY = "REMOVED"
THINGSPEAK_URL = "https://api.thingspeak.com/update"

# Twilio Configuration
TWILIO_SID = "YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_FROM = "+1234567890"  # Twilio trial number
ALERT_TO = "+91XXXXXXXXXX"   # Your mobile number

# Thresholds
TEMP_THRESHOLD = 35.0
HUM_THRESHOLD = 80.0

# Twilio client
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def get_live_location():
    """Get the user's live latitude and longitude using IP address."""
    g = geocoder.ip('me')
    if g.ok:
        return g.latlng
    else:
        return None, None

def get_weather(lat, lon):
    """Fetch live weather data from OpenWeatherMap."""
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url, timeout=5)
    data = response.json()

    temp = data['main']['temp']
    hum = data['main']['humidity']
    location = data['name']
    return temp, hum, location

def send_sms_alert(temp, hum, location):
    """Send SMS alert when threshold is exceeded."""
    msg = f"⚠️ ALERT from IoT Cloud Logger:\nLocation: {location}\nTemp: {temp:.1f}°C | Humidity: {hum:.1f}%\nThreshold exceeded!"
    try:
        client.messages.create(body=msg, from_=TWILIO_FROM, to=ALERT_TO)
        print("🚨 SMS alert sent successfully!")
    except Exception as e:
        print("❌ Failed to send SMS:", e)

def log_to_thingspeak(temp, hum, lat, lon):
    """Send data to ThingSpeak Cloud."""
    data = {
        'api_key': THINGSPEAK_API_KEY,
        'field1': temp,
        'field2': hum,
        'field3': lat,
        'field4': lon
    }
    try:
        r = requests.post(THINGSPEAK_URL, data=data, timeout=5)
        if r.status_code == 200:
            print("✅ Data logged to ThingSpeak successfully.")
        else:
            print("⚠️ ThingSpeak error:", r.status_code)
    except Exception as e:
        print("❌ Network error:", e)

def main():
    print("🌍 Starting IoT Cloud Logger (No Sensors Version)...")
    while True:
        lat, lon = get_live_location()
        if lat and lon:
            temp, hum, location = get_weather(lat, lon)
            print(f"📍 {location} | 🌡 Temp={temp:.2f}°C | 💧 Humidity={hum:.2f}% | Lat={lat}, Lon={lon}")

            log_to_thingspeak(temp, hum, lat, lon)

            if temp > TEMP_THRESHOLD or hum > HUM_THRESHOLD:
                send_sms_alert(temp, hum, location)
        else:
            print("⚠️ Unable to detect location. Retrying...")

        # ThingSpeak minimum update interval = 15 seconds
        time.sleep(20)

if __name__ == "__main__":
    main()
