import os
import json
import time
import requests
import replicate
import anthropic
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ── Credentials ──────────────────────────────────────────────
IG_TOKEN      = os.environ["INSTAGRAM_ACCESS_TOKEN"]
IG_USER_ID    = os.environ["INSTAGRAM_USER_ID"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
REPLICATE_KEY = os.environ["REPLICATE_API_TOKEN"]
NOTION_TOKEN  = os.environ["NOTION_TOKEN"]
NOTION_DB_ID  = os.environ["NOTION_DATABASE_ID"]

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── Topic bank (Claude picks one) ────────────────────────────
TOPICS = [
    "3 drills to improve freestyle technique for young swimmers",
    "How to get a water polo scholarship to a US college",
    "5 water polo tips for beginners aged 8-12",
    "Why starting swimming early gives kids a lifelong advantage",
    "What NCAA recruiters look for in a water polo athlete",
    "Morning swim workout for youth athletes",
    "How to improve your child's breaststroke in one week",
    "Water polo fitness drills you can do at home",
    "How to prepare for your first water polo tryout",
    "College recruitment timeline for youth swimmers",
    "Top 5 swimming mistakes parents don't notice",
    "How to choose the right swim program for your child",
    "Mental toughness tips for young water polo players",
    "Nutrition tips for youth aquatic athletes",
    "How water polo builds leadership skills in kids",
]

# ── Font paths: macOS first, then Ubuntu (GitHub Actions) ────
_FONT_PATHS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
]

def _font(size):
    for p in _FONT_PATHS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

# ── Step 1: Generate content with Claude ─────────────────────
def generate_content():
    print("🤖 Generating content with Claude...")
    prompt = f"""You are a social media expert for Swimnexar Aquatic Academy in Wesley Chapel, FL.
We coach youth water polo (ages 8-18) and swim team (ages 5-12).
Brand voice: expert, warm, motivating, parent-friendly.

Choose ONE topic from this list and create an Instagram carousel post:
{json.dumps(TOPICS, indent=2)}

Return ONLY valid JSON with this exact structure:
{{
  "topic": "the topic you chose",
  "slides": [
    {{"title": "Hook headline (max 8 words)", "body": ""}},
    {{"title": "Tip #1 title", "body": "2-3 sentences explanation"}},
    {{"title": "Tip #2 title", "body": "2-3 sentences explanation"}},
    {{"title": "Tip #3 title", "body": "2-3 sentences explanation"}},
    {{"title": "Ready to start?", "body": "First practice FREE at Swimnexar. Ages 8-18. Land O Lakes & Wesley Chapel, FL. swimnexar.com"}}
  ],
  "caption": "Instagram caption (150-200 words, engaging, ends with CTA and these hashtags: #waterpolo #swimming #youthsports #swimteam #wesleychapel #florida #aquatics #swimnexar #collegeprep #scholarship)",
  "image_prompt": "Photorealistic image prompt for the cover: underwater or pool scene, dramatic lighting, professional sports photography style, no text"
}}"""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

# ── Step 2: Generate cover image with Replicate ──────────────
def generate_cover_image(prompt):
    print("🎨 Generating cover image with Replicate...")
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_KEY
    output = replicate.run(
        "black-forest-labs/flux-schnell",
        input={"prompt": prompt, "num_outputs": 1, "aspect_ratio": "1:1"}
    )
    url = output[0] if isinstance(output, list) else str(output)
    r = requests.get(url)
    return Image.open(BytesIO(r.content)).convert("RGB")

# ── Step 3: Create carousel slides with Pillow ───────────────
def _wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textlength(test, font=font) < max_width:
            line = test
        else:
            lines.append(line)
            line = w
    lines.append(line)
    return lines

def create_slide(title, body, slide_num, total, bg_color=(13, 13, 13)):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    draw.rectangle([60, 60, 120, 68], fill=(212, 43, 43))
    draw.text((60, 80), f"{slide_num}/{total-1}", fill=(150, 150, 150), font=_font(28))

    font_title = _font(72)
    font_body  = _font(36)
    font_brand = _font(28)

    y = 160
    for line in _wrap_text(draw, title, font_title, W - 120):
        draw.text((60, y), line, font=font_title, fill=(255, 255, 255))
        y += 90

    if body:
        y += 20
        for line in _wrap_text(draw, body, font_body, W - 120)[:8]:
            draw.text((60, y), line, font=font_body, fill=(180, 180, 180))
            y += 50

    draw.rectangle([0, H - 80, W, H], fill=(20, 20, 20))
    draw.text((60, H - 55), "SWIMNEXAR · Aquatic Academy · swimnexar.com",
              font=font_brand, fill=(150, 150, 150))
    return img

def create_carousel_images(content, cover_img):
    images = []
    slides = content["slides"]
    total  = len(slides)
    colors = [(13,13,13), (18,22,40), (20,13,13), (13,20,13), (13,13,13)]

    for i, slide in enumerate(slides):
        if i == 0:
            img = cover_img.copy().resize((1080, 1080))
            overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 140))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)
            draw.text((60, 300), slide["title"], font=_font(80), fill=(255, 255, 255))
            draw.text((60, 1025), "SWIMNEXAR · Aquatic Academy", font=_font(32), fill=(212, 43, 43))
        else:
            img = create_slide(slide["title"], slide.get("body", ""), i, total, colors[i % len(colors)])

        path = f"/tmp/slide_{i}.jpg"
        img.save(path, "JPEG", quality=95)
        images.append(path)

    return images

# ── Step 4: Upload cover to public URL for Instagram API ─────
def upload_to_public_url(image_path):
    """Instagram Graph API requires a publicly accessible image URL."""
    print("⬆️  Uploading cover image to public host...")
    with open(image_path, "rb") as f:
        r = requests.post(
            "https://0x0.st",
            files={"file": ("cover.jpg", f, "image/jpeg")},
            timeout=30,
        )
    if r.status_code == 200:
        url = r.text.strip()
        print(f"  URL: {url}")
        return url
    raise RuntimeError(f"Upload failed ({r.status_code}): {r.text[:200]}")

# ── Step 5: Schedule Instagram post ──────────────────────────
def post_to_instagram(images, caption):
    """Creates a scheduled post (24 h from now). Open Instagram → Profile →
    Scheduled content to add music and publish early if you want."""
    print("📅 Scheduling Instagram post for 24 hours from now...")
    base = "https://graph.instagram.com/v21.0"

    cover_url = upload_to_public_url(images[0])

    scheduled_ts = int(time.time()) + 86400  # 24 hours from now

    r = requests.post(f"{base}/{IG_USER_ID}/media", data={
        "image_url":              cover_url,
        "caption":                caption,
        "published":              "false",
        "scheduled_publish_time": scheduled_ts,
        "access_token":           IG_TOKEN,
    })
    container = r.json()
    print(f"Container: {container}")

    if "id" not in container:
        print(f"❌ Container creation failed: {container}")
        return None

    r2 = requests.post(f"{base}/{IG_USER_ID}/media_publish", data={
        "creation_id":  container["id"],
        "access_token": IG_TOKEN,
    })
    result = r2.json()
    scheduled_at = datetime.fromtimestamp(scheduled_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"Scheduled for {scheduled_at}: {result}")
    return result.get("id")

# ── Step 6: Log to Notion ─────────────────────────────────────
def log_to_notion(content, post_id):
    print("📝 Logging to Notion...")
    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers={
            "Authorization":  f"Bearer {NOTION_TOKEN}",
            "Content-Type":   "application/json",
            "Notion-Version": "2022-06-28",
        },
        json={
            "parent": {"database_id": NOTION_DB_ID},
            "properties": {
                "Name":        {"title":     [{"text": {"content": content["topic"]}}]},
                "Status":      {"select":    {"name": "Scheduled" if post_id else "Error"}},
                "Topic":       {"rich_text": [{"text": {"content": content["topic"]}}]},
                "Caption":     {"rich_text": [{"text": {"content": content["caption"][:2000]}}]},
                "Posted Date": {"date":      {"start": datetime.now().isoformat()}},
            },
        },
    )
    print(f"Notion: {r.status_code}")

# ── Main ──────────────────────────────────────────────────────
def main():
    print("🚀 Swimnexar Instagram Bot starting...")

    content   = generate_content()
    print(f"✅ Topic: {content['topic']}")

    cover_img = generate_cover_image(content["image_prompt"])
    images    = create_carousel_images(content, cover_img)
    print(f"✅ Created {len(images)} slides")

    post_id = post_to_instagram(images, content["caption"])
    print(f"✅ Scheduled! ID: {post_id}")
    print("👉 Open Instagram → Profile → Scheduled content → add music → publish")

    log_to_notion(content, post_id)
    print("🎉 Done!")

if __name__ == "__main__":
    main()
