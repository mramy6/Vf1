
import json
import requests
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

TOKEN = '7617376104:AAFiF3UEW-FD0OOUkgcPq4piJl3U-McwMTA'

NUMBER, PASSWORD = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""👋 Welcome to Free Gifts Bot

💚 TEAM Abowaged
📢 We are happy to have you here. Join our group:
🔗 https://t.me/mabowaged_eg

🤖 تم صنع البوت بواسطة: @mabowaged_eg
""")
    await update.message.reply_text("📱 Please send your phone number")
    return NUMBER

async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['number'] = update.message.text.strip()
    await update.message.reply_text("ابعت كلمة السر 🔐")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = context.user_data.get('number')
    password = update.message.text.strip()

    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ جاري تنفيذ العملية...")

    url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    payload = {
        'username': number,
        'password': password,
        'grant_type': "password",
        'client_secret': "95fd95fb-7489-4958-8ae6-d31a525cd20a",
        'client_id': "ana-vodafone-app"
    }

    headers = {
        'User-Agent': "okhttp/4.11.0",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip",
        'silentLogin': "true",
        'x-dynatrace': "MT_3_24_1131333938_226-0_a556db1b-4506-43f3-854a-1d2527767923_0_193_104",
        'x-agent-operatingsystem': "13",
        'clientId': "AnaVodafoneAndroid",
        'Accept-Language': "ar",
        'x-agent-device': "Xiaomi 21061119AG",
        'x-agent-version': "2024.12.1",
        'x-agent-build': "946",
        'digitalId': "28RI9U7IG5T6D"
    }

    response = requests.post(url, data=payload, headers=headers)
    result = response.json()
    token = result.get('access_token')
    if not token:
        await update.message.reply_text("❌ الرقم أو الباسورد غير صحيح.")
        return ConversationHandler.END

    url = f"https://web.vodafone.com.eg/services/dxl/promo/promotion?@type=Promo&$.context.type=5G_Promo&$.characteristics%5B@name%3DcustomerNumber%5D.value={number}"
    headers.update({
        'User-Agent': "vodafoneandroid",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Authorization': f"Bearer {token}",
        'msisdn': number,
        'clientId': "WebsiteConsumer",
        'channel': "APP_PORTAL",
        'Content-Type': "application/json",
        'X-Requested-With': "com.emeint.android.myservices",
        'Referer': "https://web.vodafone.com.eg/portal/bf/5gGame"
    })

    data = requests.get(url, headers=headers).json()
    current_level = None
    scores = []

    for item in data:
        for characteristic in item.get("characteristics", []):
            name = characteristic.get("name")
            value = characteristic.get("value")
            if name == "currentLevel":
                current_level = value
            elif name == "scores":
                scores = list(map(int, value.split(',')))

    level = current_level if current_level else "1"
    scores = max(scores) if scores else "50"

    url = "https://web.vodafone.com.eg/services/dxl/promo/promotion"
    payload = {
        "@type": "Promo",
        "channel": {"id": "APP_PORTAL"},
        "context": {"type": "5G_Promo"},
        "pattern": [
            {
                "characteristics": [
                    {"name": "level", "value": level},
                    {"name": "score", "value": scores},
                    {"name": "customerNumber", "value": number}
                ]
            }
        ]
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    try:
        response_data = response.json()
        promo_id = response_data['id']
        mg = response_data["characteristics"][0]["value"]
    except:
        await update.message.reply_text("❗ يبدو أنك أخذت الهدية اليوم بالفعل.")
        return ConversationHandler.END

    url = f"https://web.vodafone.com.eg/services/dxl/promo/promotion/{promo_id}"
    payload = {
        "@type": "Promo",
        "channel": {"id": "APP_PORTAL"},
        "context": {"type": "5G_Promo"},
        "pattern": [
            {
                "characteristics": [
                    {"name": "customerNumber", "value": number}
                ]
            }
        ]
    }

    response = requests.patch(url, data=json.dumps(payload), headers=headers)
    if response.status_code == 204:
        await update.message.reply_text(f"✅ تم إضافة {mg} ميجا بنجاح 🔥")
    else:
        await update.message.reply_text("⚠️ حدث خطأ أثناء تفعيل الهدية.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_number)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_handler)
    print("🤖 Bot is running as عبواجد...")
    app.run_polling()
