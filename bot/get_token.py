import requests
import sys

CLIENT_ID     = "1945449166095595"
CLIENT_SECRET = "fcc678c1137e9ed80da161ef4472683d"
REDIRECT_URI  = "https://swimnexar.vercel.app/"

OAUTH_URL = (
    f"https://www.instagram.com/oauth/authorize"
    f"?force_reauth=true"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code"
    f"&scope=instagram_business_basic"
    f"%2Cinstagram_business_manage_messages"
    f"%2Cinstagram_business_manage_comments"
    f"%2Cinstagram_business_content_publish"
    f"%2Cinstagram_business_manage_insights"
)

if len(sys.argv) > 1:
    raw = sys.argv[1].strip()
    print(f"📋 Обмениваю код...")
else:
    import webbrowser
    print("\n🔗 Открываю браузер для авторизации...\n")
    webbrowser.open(OAUTH_URL)
    print("После нажатия Allow скопируй команду с сайта и запусти заново.")
    sys.exit(0)

# strip full URL if pasted (Instagram appends "#_" after the code)
if "code=" in raw:
    raw = raw.split("code=")[1].split("#")[0].strip()

print(f"\n⏳ Обмениваю код на токен...")
print(f"   code: {raw[:12]}…{raw[-6:]}  (длина {len(raw)})")
print(f"   redirect_uri: {REDIRECT_URI}")

r = requests.post("https://api.instagram.com/oauth/access_token", data={
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type":    "authorization_code",
    "redirect_uri":  REDIRECT_URI,
    "code":          raw,
})

data = r.json()
if "access_token" in data:
    short_token = data["access_token"]
    user_id     = data["user_id"]
    print(f"\n✅ Краткосрочный токен получен!")
    print(f"User ID: {user_id}")

    # Exchange for long-lived token (60 days)
    r2 = requests.get(
        "https://graph.instagram.com/access_token",
        params={
            "grant_type":        "ig_exchange_token",
            "client_secret":     CLIENT_SECRET,
            "access_token":      short_token,
        }
    )
    d2 = r2.json()
    if "access_token" in d2:
        long_token = d2["access_token"]
        print(f"\n🎉 Долгосрочный токен (60 дней):")
        print(f"\n{long_token}\n")
        print(f"User ID: {user_id}")
        with open("instagram_token.txt", "w") as f:
            f.write(f"ACCESS_TOKEN={long_token}\n")
            f.write(f"USER_ID={user_id}\n")
        print("✅ Сохранено в instagram_token.txt")
    else:
        print(f"Ошибка long-lived: {d2}")
else:
    print(f"Ошибка: {data}")
