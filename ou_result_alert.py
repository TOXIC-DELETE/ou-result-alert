import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3
import time
import os

# Hide the temporary SSL warning
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# ==============================
# SETTINGS
# ==============================

OU_URL = "https://www.osmania.ac.in/examination-results.php"

# IMPORTANT:
# Put your BotFather token between the quotes.
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

CHAT_ID = "1807465704"

# Check every 5 minutes
CHECK_INTERVAL = 5 * 60

# File used to remember that the result was already announced
NOTIFIED_FILE = "result_notified.txt"


# ==============================
# TELEGRAM
# ==============================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(
            url,
            data=data,
            timeout=20
        )

        response.raise_for_status()

        print("📱 Telegram notification sent!")
        return True

    except requests.RequestException as e:
        print("⚠️ Telegram notification failed:")
        print(e)
        return False


# ==============================
# CHECK OU WEBSITE
# ==============================

def check_ou_results():

    print("\n🔎 Checking OU results...")

    try:

        response = requests.get(
            OU_URL,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            },

            # Temporary workaround for OU SSL issue
            verify=False
        )

        print("Website status:", response.status_code)

        response.raise_for_status()

    except requests.RequestException as e:

        print("⚠️ Could not access OU website.")
        print("Error:", e)

        return None


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    # Search every table row
    for row in soup.find_all("tr"):

        result_text = row.get_text(
            " ",
            strip=True
        )

        text = result_text.lower()

        # Remove dots so things like B.E. are also detected
        clean_text = text.replace(".", "")


        # Required conditions
        has_be_aicte = "be aicte" in clean_text

        has_vi_sem = (
            "vi sem" in clean_text
            or
            "vi semester" in clean_text
        )

        has_regular = "regular" in clean_text


        # If all three are present
        if (
            has_be_aicte
            and has_vi_sem
            and has_regular
        ):

            link = row.find("a")

            result_url = None

            if link and link.get("href"):

                result_url = urljoin(
                    OU_URL,
                    link.get("href")
                )


            return {
                "name": result_text,
                "url": result_url
            }


    return None


# ==============================
# DUPLICATE PROTECTION
# ==============================

def already_notified(result):

    if not os.path.exists(NOTIFIED_FILE):
        return False


    try:

        with open(
            NOTIFIED_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            previous_result = file.read().strip()


        return previous_result == result["name"]


    except Exception:

        return False


def save_notification(result):

    with open(
        NOTIFIED_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(result["name"])


# ==============================
# START
# ==============================

print("==========================================")
print("        OU RESULT ALERT SYSTEM")
print("==========================================")
print()
print("🎓 Monitoring:")
print("BE AICTE + VI SEM + REGULAR")
print()
print("⏱️ Checking every 5 minutes.")
print("📱 Telegram notifications: ENABLED")
print("🛑 Press CTRL + C to stop.")
print()


# ==============================
# MAIN MONITOR
# ==============================

# ==============================
# RUN ONE CHECK
# ==============================

result = check_ou_results()

if result:

    print()
    print("==========================================")
    print("🎉 RESULT FOUND!")
    print("==========================================")

    print("Result:")
    print(result["name"])

    print()
    print("Link:")
    print(result["url"])

    if already_notified(result):

        print()
        print("ℹ️ This result was already notified.")
        print("No Telegram message sent.")

    else:

        message = (
            "🎓 OU RESULT ALERT!\n\n"
            "🎉 Your result appears to be released!\n\n"
            f"{result['name']}\n\n"
        )

        if result["url"]:

            message += (
                "🔗 Official OU Result:\n"
                f"{result['url']}"
            )

        else:

            message += (
                "Please check the official OU results page:\n"
                f"{OU_URL}"
            )

        sent = send_telegram(message)

        if sent:

            save_notification(result)

            print()
            print("✅ Telegram notification sent and recorded.")

else:

    print()
    print("❌ VI SEM REGULAR result not found yet.")
    print("Waiting for BE AICTE + VI SEM + REGULAR.")

print()
print("✅ Check finished.")
