import os
import re
import json
import time
import requests
import replicate
import anthropic
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO

# ── Credentials ──────────────────────────────────────────────
IG_TOKEN      = os.environ["INSTAGRAM_ACCESS_TOKEN"]
IG_USER_ID    = os.environ["INSTAGRAM_USER_ID"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
REPLICATE_KEY = os.environ["REPLICATE_API_TOKEN"]
NOTION_TOKEN  = os.environ["NOTION_TOKEN"]
NOTION_DB_ID  = os.environ["NOTION_DATABASE_ID"]

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

W, H   = 1080, 1080
RED    = (212, 43, 43)
WHITE  = (255, 255, 255)
GRAY   = (150, 150, 150)
LGRAY  = (90, 90, 90)
DARK   = (13, 13, 13)
DARKER = (8, 8, 8)

# ── Topic bank ───────────────────────────────────────────────
TOPICS = [
    # Technique & drills
    "3 drills to improve freestyle technique for young swimmers",
    "3 water polo passing drills every beginner needs",
    "5 water polo tips for beginners aged 8-12",
    "How to do a perfect flip turn — step by step for kids",
    "Morning swim workout for youth athletes",
    "How to improve your child's breaststroke in one week",
    "Water polo fitness drills you can do at home",
    "How to prepare for your first water polo tryout",
    "5 kick drills every young swimmer needs to master",
    "Top 5 swimming mistakes parents don't notice",
    "Water polo shooting technique for beginners aged 8-12",
    "How to teach proper breathing in freestyle to young swimmers",
    "Best backstroke drills for kids who are just starting out",
    # Parent & lifestyle
    "Why starting swimming early gives kids a lifelong advantage",
    "How to choose the right swim program for your child",
    "Mental toughness tips for young water polo players",
    "Nutrition tips for youth aquatic athletes",
    "How water polo builds leadership skills in kids",
    # College & recruitment (~1x/week)
    "How to get a water polo scholarship to a US college",
    "What NCAA recruiters look for in a water polo athlete",
    "College recruitment timeline for youth swimmers",
    "How to build a recruiting profile for water polo by age 14",
]

# ── Fonts ─────────────────────────────────────────────────────
_FONT_CACHE: dict = {}

_FONT_URLS = {
    "bold":      "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "extrabold": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf",
    "regular":   "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
}
_FONT_SYSTEM = {
    "bold":      ["/System/Library/Fonts/Helvetica.ttc",
                  "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "extrabold": ["/System/Library/Fonts/Helvetica.ttc",
                  "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
    "regular":   ["/System/Library/Fonts/Helvetica.ttc",
                  "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}

def _font_path(weight="bold"):
    cache = f"/tmp/swimnexar_{weight}.ttf"
    if os.path.exists(cache):
        return cache
    for p in _FONT_SYSTEM[weight]:
        if os.path.exists(p):
            return p
    try:
        r = requests.get(_FONT_URLS[weight], timeout=20)
        if r.status_code == 200:
            with open(cache, "wb") as f:
                f.write(r.content)
            return cache
    except Exception:
        pass
    return None

def _font(size, weight="bold"):
    key = (size, weight)
    if key not in _FONT_CACHE:
        p = _font_path(weight)
        try:
            _FONT_CACHE[key] = ImageFont.truetype(p, size) if p else ImageFont.load_default()
        except Exception:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]

# ── Logo ──────────────────────────────────────────────────────
_LOGO_CACHE: dict = {}

def _logo(width=160):
    if width in _LOGO_CACHE:
        return _LOGO_CACHE[width]
    try:
        local = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(local):
            img = Image.open(local).convert("RGBA")
        else:
            r = requests.get(
                "https://swimnexar.com/wp-content/uploads/2025/10/header-title-scaled-129x47.png",
                timeout=10)
            img = Image.open(BytesIO(r.content)).convert("RGBA")
        # Make all visible pixels white (logo is dark, we need it white on dark bg)
        img.putdata([(255, 255, 255, p[3]) if p[3] > 10 else (0, 0, 0, 0)
                     for p in img.getdata()])
        h = int(img.height * width / img.width)
        result = img.resize((width, h), Image.LANCZOS)
        _LOGO_CACHE[width] = result
        return result
    except Exception as e:
        print(f"Logo load error: {e}")
        return None

def _paste_logo(img, x, y, width=155):
    lg = _logo(width)
    if lg:
        img.paste(lg, (x, y), lg)

# ── Drawing helpers ───────────────────────────────────────────
def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textlength(test, font=font) < max_w:
            line = test
        else:
            lines.append(line)
            line = w
    lines.append(line)
    return [l for l in lines if l]

def _dots(draw, total, active, cx, y, r=6, gap=22):
    sx = cx - ((total - 1) * gap) // 2
    for i in range(total):
        fill = RED if i == active else LGRAY
        bx = sx + i * gap
        draw.ellipse([bx - r, y - r, bx + r, y + r], fill=fill)

# ── Step 1: Generate content with Claude ─────────────────────
def _pick_topic():
    import random
    return random.choice(TOPICS)

def _is_waterpolo(topic):
    return "water polo" in topic.lower()

def generate_content():
    print("🤖 Generating content with Claude...")
    topic = _pick_topic()
    ages  = "7–18" if _is_waterpolo(topic) else "5–18"
    prompt = f"""You are a social media expert for Nexar Aquatic Academy in Wesley Chapel, FL.
You must create a post about this specific topic: "{topic}"
We coach youth water polo (ages 7-18) and swim team (ages 5-18).
Always refer to the academy as "Nexar Aquatic Academy" — never "Nexar Water Polo Club", "Nexar Swim Team", or any other variation.
Brand voice: professional, warm, and knowledgeable. Like an experienced coach who genuinely cares about each athlete's development. Confident but never arrogant.
IMPORTANT: All content must be written in American English only. Target audience is American parents and youth athletes.

Style rules:
- Write in complete, grammatically correct sentences — no fragments, no slang
- Hook slide: bold statement or surprising fact, max 7 words, clear and polished
- Tip slides: lead with the action, then explain — specific and concrete (say "6 kicks per arm stroke" not "kick properly")
- Skip filler phrases like "it's important to", "make sure to", "don't forget"
- Refer to athletes as "young athletes", "swimmers", or "players" — never "your kids", "your child", "your athlete"
- Do NOT address parents directly ("you as a parent", "your child needs") — share knowledge as a coach, not as a teacher lecturing
- Write as if sharing expertise with the community, not giving instructions to parents
- CTA slide: warm and welcoming, never pushy or salesy

Return ONLY valid JSON with this exact structure:
{{
  "topic": "{topic}",
  "slides": [
    {{"title": "Hook headline (max 7 words)", "body": ""}},
    {{"title": "Short tip title (max 6 words)", "body": "1-2 sentences max — concrete and specific"}},
    {{"title": "Short tip title (max 6 words)", "body": "1-2 sentences max — concrete and specific"}},
    {{"title": "Short tip title (max 6 words)", "body": "1-2 sentences max — concrete and specific"}},
    {{"title": "Come Try It Free", "body": "First practice FREE · Ages {ages} · Land O' Lakes & Wesley Chapel, FL · swimnexar.com"}}
  ],
  "caption": "2-3 short sentences max. One hook, one value line, one CTA (e.g. 'First practice is free — link in bio'). No long paragraphs. Hashtags on a new line: #waterpolo #swimming #youthsports #swimteam #wesleychapel #florida #aquatics #swimnexar #collegeprep #scholarship",
  "image_prompt": "Photorealistic dramatic sports photo related to the topic above. Professional athletics photography, moody underwater lighting or golden hour pool light, no text, cinematic"
}}"""

    for attempt in range(3):
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # Extract JSON block robustly
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group()
        elif text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            content = json.loads(text.strip())
            # Normalize brand name everywhere
            brand_fix = re.compile(r'Nexar (Water Polo Club|Swim Team|Water Polo Team|Aquatics)', re.IGNORECASE)
            content["caption"] = brand_fix.sub("Nexar Aquatic Academy", content["caption"])
            return content
        except json.JSONDecodeError as e:
            print(f"JSON parse error (attempt {attempt+1}): {e}")
            if attempt == 2:
                raise

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

# ── Step 3: Create carousel slides ───────────────────────────
def _make_cover(slide, cover_img, total):
    """Slide 0: AI photo background with logo + title overlay."""
    img = cover_img.copy().resize((W, H), Image.LANCZOS)

    # Dark gradient overlay — heavier at bottom for text legibility
    overlay = Image.new("RGBA", (W, H))
    ov_draw = ImageDraw.Draw(overlay)
    for y in range(H):
        t = y / H
        alpha = int(80 + 140 * t)   # 80 at top → 220 at bottom
        ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Brand name — top left
    draw.text((44, 44), "NEXAR AQUATIC ACADEMY", font=_font(28, "bold"), fill=WHITE)

    # Red accent line — left edge of title area
    draw.rectangle([44, 340, 52, 490], fill=RED)

    # Title — large, bold
    title_font = _font(76, "extrabold")
    title_lines = _wrap(draw, slide["title"], title_font, W - 130)
    y = 350
    for line in title_lines[:3]:
        draw.text((68, y), line, font=title_font, fill=WHITE)
        y += 94

    # Bottom strip
    draw.rectangle([0, H - 72, W, H], fill=(0, 0, 0, 180))
    draw = ImageDraw.Draw(img)
    draw.text((44, H - 50), "swimnexar.com", font=_font(26, "regular"), fill=GRAY)

    # Dots — bottom right area
    _dots(draw, total, 0, W - 110, H - 36)

    return img.convert("RGB")

def _make_content_slide(slide, idx, total):
    """Slides 1–3: dark branded layout with faded number + logo."""
    img = Image.new("RGB", (W, H), DARK)
    draw = ImageDraw.Draw(img)

    # Faded giant number (design element)
    ghost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ghost)
    gd.text((-15, 150), str(idx), font=_font(380, "extrabold"), fill=(255, 255, 255, 16))
    img = Image.alpha_composite(img.convert("RGBA"), ghost).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Top red bar
    draw.rectangle([0, 0, W, 6], fill=RED)

    # Slide counter — top left
    cnt_font = _font(28, "bold")
    draw.text((44, 26), f"{idx:02d}", font=cnt_font, fill=RED)
    offset = int(draw.textlength(f"{idx:02d}", font=cnt_font)) + 10
    draw.text((44 + offset, 26), f"/ {total - 1:02d}", font=cnt_font, fill=LGRAY)

    # Brand name — top right
    draw.text((W - 44, 26), "NEXAR AQUATIC ACADEMY", font=_font(24, "bold"), fill=WHITE, anchor="ra")

    # Title
    title_font = _font(66, "extrabold")
    title_lines = _wrap(draw, slide["title"], title_font, W - 100)
    y = 195
    for line in title_lines[:2]:
        draw.text((44, y), line, font=title_font, fill=WHITE)
        y += 82

    # Red accent line under title
    draw.rectangle([44, y + 14, 104, y + 19], fill=RED)
    y += 52

    # Body text
    if slide.get("body"):
        body_font = _font(34, "regular")
        for line in _wrap(draw, slide["body"], body_font, W - 90)[:7]:
            draw.text((44, y), line, font=body_font, fill=(165, 165, 165))
            y += 52

    # Bottom bar
    draw.rectangle([0, H - 72, W, H], fill=DARKER)
    draw.text((44, H - 50), "swimnexar.com", font=_font(24, "regular"), fill=LGRAY)
    _dots(draw, total, idx, W // 2, H - 36)

    return img

def _make_cta_slide(slide, total):
    """Last slide: CTA with centered logo + free trial pill."""
    img = Image.new("RGB", (W, H), (10, 8, 8))
    draw = ImageDraw.Draw(img)

    # Top red bar (thicker)
    draw.rectangle([0, 0, W, 10], fill=RED)

    # Logo — centered, bigger
    lg = _logo(210)
    if lg:
        lx = (W - 210) // 2
        img.paste(lg, (lx, 90), lg)
    draw = ImageDraw.Draw(img)

    # Title
    title_font = _font(72, "extrabold")
    draw.text((W // 2, 290), slide["title"], font=title_font, fill=WHITE, anchor="mm")

    # "FIRST PRACTICE FREE" pill
    pill_font = _font(30, "bold")
    pill_text = "FIRST PRACTICE FREE"
    pw = int(draw.textlength(pill_text, font=pill_font))
    px = (W - pw - 64) // 2
    draw.rounded_rectangle([px, 360, px + pw + 64, 420], radius=30, fill=RED)
    draw.text((W // 2, 390), pill_text, font=pill_font, fill=WHITE, anchor="mm")

    # Body details (skip swimnexar.com — shown separately below)
    body = slide.get("body", "")
    body_font = _font(32, "regular")
    y = 470
    for part in body.split("·"):
        part = part.strip()
        if part and "swimnexar.com" not in part:
            draw.text((W // 2, y), part, font=body_font, fill=(180, 180, 180), anchor="mm")
            y += 50

    # Website prominent
    draw.text((W // 2, y + 40), "swimnexar.com", font=_font(46, "bold"), fill=WHITE, anchor="mm")

    # Bottom
    draw.rectangle([0, H - 72, W, H], fill=DARKER)
    _dots(draw, total, total - 1, W // 2, H - 36)

    return img

def create_carousel_images(content, cover_img):
    images = []
    slides = content["slides"]
    total  = len(slides)

    for i, slide in enumerate(slides):
        if i == 0:
            img = _make_cover(slide, cover_img, total)
        elif i == total - 1:
            img = _make_cta_slide(slide, total)
        else:
            img = _make_content_slide(slide, i, total)

        path = f"/tmp/slide_{i}.jpg"
        img.save(path, "JPEG", quality=95)
        images.append(path)
        print(f"  Slide {i+1}/{total} saved")

    return images

# ── Step 4: Upload cover to public URL for Instagram API ─────
def _try_litterbox(path):
    with open(path, "rb") as f:
        r = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": "72h"},
            files={"fileToUpload": ("cover.jpg", f, "image/jpeg")},
            timeout=30,
        )
    if r.status_code == 200 and r.text.strip().startswith("https://"):
        return r.text.strip()
    raise RuntimeError(f"litterbox: {r.status_code} {r.text[:100]}")

def _try_uguu(path):
    with open(path, "rb") as f:
        r = requests.post(
            "https://uguu.se/upload.php",
            files={"files[]": ("cover.jpg", f, "image/jpeg")},
            timeout=30,
        )
    if r.status_code == 200:
        return r.json()["files"][0]["url"]
    raise RuntimeError(f"uguu: {r.status_code} {r.text[:100]}")

def _try_transfersh(path):
    with open(path, "rb") as f:
        r = requests.put(
            "https://transfer.sh/swimnexar_cover.jpg",
            data=f, headers={"Max-Days": "1"}, timeout=30,
        )
    if r.status_code == 200:
        return r.text.strip()
    raise RuntimeError(f"transfer.sh: {r.status_code} {r.text[:100]}")

def upload_to_public_url(image_path):
    print("⬆️  Uploading cover image...")
    for fn in [_try_litterbox, _try_uguu, _try_transfersh]:
        try:
            url = fn(image_path)
            print(f"  URL: {url}")
            return url
        except Exception as e:
            print(f"  {e} — trying next service...")
    raise RuntimeError("All upload services failed")

# ── Step 5: Post carousel to Instagram ───────────────────────
def post_to_instagram(images, caption):
    print("📱 Posting carousel to Instagram...")
    base = "https://graph.instagram.com/v21.0"

    # Upload all slides
    urls = []
    for i, path in enumerate(images):
        print(f"  Uploading slide {i+1}/{len(images)}...")
        urls.append(upload_to_public_url(path))

    # Create a media container for each slide
    print("📦 Creating child containers...")
    child_ids = []
    for i, url in enumerate(urls):
        r = requests.post(f"{base}/{IG_USER_ID}/media", data={
            "image_url":        url,
            "is_carousel_item": "true",
            "access_token":     IG_TOKEN,
        })
        data = r.json()
        print(f"  Slide {i+1}: {data}")
        if "id" not in data:
            print(f"❌ Child container failed: {data}")
            return None
        child_ids.append(data["id"])

    # Create carousel container
    print("🎠 Creating carousel container...")
    r = requests.post(f"{base}/{IG_USER_ID}/media", data={
        "media_type":   "CAROUSEL",
        "children":     ",".join(child_ids),
        "caption":      caption,
        "access_token": IG_TOKEN,
    })
    carousel = r.json()
    print(f"Carousel: {carousel}")

    if "id" not in carousel:
        print(f"❌ Carousel creation failed: {carousel}")
        return None

    # Publish
    r2 = requests.post(f"{base}/{IG_USER_ID}/media_publish", data={
        "creation_id":  carousel["id"],
        "access_token": IG_TOKEN,
    })
    result = r2.json()
    print(f"Published: {result}")
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

    log_to_notion(content, post_id)
    print("🎉 Done!")

if __name__ == "__main__":
    main()
