import os
import re
import json
import time
import base64
import random
import requests
import anthropic
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO

# ── Credentials ──────────────────────────────────────────────
IG_TOKEN      = os.environ["INSTAGRAM_ACCESS_TOKEN"]
IG_USER_ID    = os.environ["INSTAGRAM_USER_ID"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
PEXELS_KEY    = os.environ["PEXELS_API_KEY"]
NOTION_TOKEN  = os.environ.get("NOTION_TOKEN")        # optional — logging only
NOTION_DB_ID  = os.environ.get("NOTION_DATABASE_ID")  # optional — logging only

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

W, H   = 1080, 1080
RED    = (212, 43, 43)
WHITE  = (255, 255, 255)
GRAY   = (150, 150, 150)
LGRAY  = (90, 90, 90)
DARK   = (13, 13, 13)
DARKER = (8, 8, 8)

# ── Used-topics state (local file, committed back by CI) ─────
# Notion logging used to be the source of truth here, but its writes were
# failing (HTTP 400), so the dedup always saw an empty history and repeated
# topics. State now lives in a committed JSON file — reliable and self-contained.
STATE_FILE = os.path.join(os.path.dirname(__file__), "posted_topics.json")

def _load_used_topics():
    """Read previously posted topics from the committed state file."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("topics", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _record_used_topic(topic):
    """Append a freshly posted topic to the state file (CI commits it back)."""
    used = _load_used_topics()
    if topic not in used:
        used.append(topic)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, indent=2, ensure_ascii=False)
    print(f"📒 Recorded topic — history now {len(used)} entries")

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
    used = _load_used_topics()
    print(f"📋 Used topics so far: {len(used)}/{len(TOPICS)}")
    available = [t for t in TOPICS if t not in used]
    if not available:
        print("🔄 All topics used — resetting cycle")
        available = TOPICS
    topic = random.choice(available)
    return topic

def _is_waterpolo(topic):
    return "water polo" in topic.lower()

def generate_content():
    print("🤖 Generating content with Claude...")
    topic = _pick_topic()
    waterpolo = _is_waterpolo(topic)
    ages  = "7–18" if waterpolo else "5–18"
    sport = "water polo" if waterpolo else "swimming"
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
  "pexels_query": "2-4 word real-photo search query for a stock photo site, matching the sport ({sport}) and topic. It must return action photos of a visible athlete — e.g. 'water polo match', 'freestyle swimmer racing', 'swimmer underwater', 'competitive swimming'. Do NOT use the word 'pool' on its own (it returns billiards photos) and avoid equipment-only terms like 'lane ropes'. No people's names, no text overlays."
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

# ── Step 2: Fetch a real cover photo from Pexels ─────────────
# Note: avoid the bare word "pool" — Pexels returns billiards photos for it.
_PEXELS_FALLBACKS = {
    True:  ["water polo match", "water polo players", "water polo game", "water polo athlete"],
    False: ["competitive swimmer", "swimmer racing", "freestyle swimming", "swimming competition"],
}

def _pexels_search(query):
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": query, "per_page": 15, "orientation": "landscape"},
        timeout=15,
    )
    return r.json().get("photos", [])

def _photo_fits(photo, topic, sport):
    """Ask Claude (vision) whether this photo actually matches the post."""
    try:
        thumb = requests.get(photo["src"]["medium"], timeout=15).content
        b64 = base64.standard_b64encode(thumb).decode()
        resp = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": (
                    f'This photo will be the cover image of a youth {sport} social media post '
                    f'titled "{topic}". Answer YES only if ALL of these hold: '
                    f'(1) it clearly shows at least one real {sport} athlete actively swimming or '
                    f'playing water polo in the water — a visible person in action, not an empty '
                    f'pool, lane ropes, equipment, or water alone; '
                    f'(2) it genuinely depicts {sport} (not billiards, not a hot tub/spa, not a '
                    f'beach or open water leisure scene); '
                    f'(3) no babies/bathtubs, no unrelated objects, no overlaid text or watermarks. '
                    f'Otherwise answer NO. Reply with only YES or NO.'
                )},
            ]}],
        )
        ans = resp.content[0].text.strip().upper()
        print(f"    vision check: {ans[:3]} — {photo.get('url', '')}")
        return ans.startswith("Y")
    except Exception as e:
        print(f"    vision check failed ({e}) — accepting photo")
        return True

# Used-photos state (committed back by CI) so the same cover never repeats.
PHOTO_STATE_FILE = os.path.join(os.path.dirname(__file__), "used_photos.json")

def _load_used_photos():
    try:
        with open(PHOTO_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data if isinstance(data, list) else data.get("ids", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def _record_used_photo(photo_id):
    used = _load_used_photos()
    used.add(photo_id)
    with open(PHOTO_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(used), f, indent=2)
    print(f"📸 Recorded photo {photo_id} — {len(used)} photos used so far")

def _download(photo):
    r = requests.get(photo["src"]["large2x"], timeout=30)
    return Image.open(BytesIO(r.content)).convert("RGB")

def fetch_cover_photo(query, is_waterpolo, topic):
    """Pick a Pexels photo that (a) hasn't been used before and (b) vision-fits the post.

    Returns (Image, photo_id). The id is recorded only after a successful post.
    """
    sport = "water polo" if is_waterpolo else "swimming"
    used = _load_used_photos()
    print(f"📷 Searching Pexels: {query}  (avoiding {len(used)} already-used photos)")
    candidates = _pexels_search(query)
    for fb in _PEXELS_FALLBACKS[is_waterpolo]:
        print(f"  Adding fallback query: {fb}")
        candidates += _pexels_search(fb)
    # De-dup this candidate list by photo id
    seen, uniq = set(), []
    for p in candidates:
        if p["id"] not in seen:
            seen.add(p["id"])
            uniq.append(p)
    if not uniq:
        raise RuntimeError(f"Pexels returned no photos for '{query}' or fallbacks")
    random.shuffle(uniq)

    def _first_passing(cands):
        for p in cands:
            if _photo_fits(p, topic, sport):
                return p
        return None

    fresh = [p for p in uniq if p["id"] not in used]
    # Prefer a never-used photo that passes vision; only then fall back to a used one.
    chosen = _first_passing(fresh[:12])
    if chosen is None:
        print("  ⚠️ No fresh photo passed the vision check — falling back to used photos")
        chosen = _first_passing([p for p in uniq if p["id"] in used][:8]) or (fresh or uniq)[0]

    if chosen["id"] in used:
        print(f"  ⚠️ Reusing photo {chosen['id']} (no fresh match available)")
    print(f"  ✅ Chosen: photo {chosen['id']} by {chosen.get('photographer', '?')} — {chosen.get('url', '')}")
    return _download(chosen), chosen["id"]

# ── Step 3: Create carousel slides ───────────────────────────
def _make_cover(slide, cover_img, total):
    """Slide 0: real photo background with logo + title overlay."""
    # Center-crop to square so landscape stock photos aren't squished.
    img = ImageOps.fit(cover_img, (W, H), Image.LANCZOS, centering=(0.5, 0.4))

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

_UPLOAD_HOSTS = [_try_litterbox, _try_uguu, _try_transfersh]

# ── Step 5: Post carousel to Instagram ───────────────────────
def _create_child_container(base, path, slide_no, total):
    """Upload one slide and create its IG carousel child container.

    Instagram fetches the image from the public URL itself, and some hosts are
    intermittently un-fetchable by IG (error 9004). So on a media-fetch failure
    we re-upload to the next host and retry, instead of aborting the whole post.
    """
    tried = []
    for host in _UPLOAD_HOSTS:
        try:
            url = host(path)
        except Exception as e:
            print(f"  Slide {slide_no}/{total}: upload via {host.__name__} failed: {e}")
            continue
        print(f"  Slide {slide_no}/{total} → {url} ({host.__name__})")
        r = requests.post(f"{base}/{IG_USER_ID}/media", data={
            "image_url":        url,
            "is_carousel_item": "true",
            "access_token":     IG_TOKEN,
        })
        data = r.json()
        if "id" in data:
            return data["id"]
        err = data.get("error", {})
        msg = err.get("error_user_msg") or err.get("message") or data
        print(f"  ⚠️  Instagram rejected {host.__name__}: {msg} — trying next host")
        tried.append(host.__name__)
    raise RuntimeError(
        f"Slide {slide_no}: all upload hosts failed or were unreachable by Instagram "
        f"(tried: {', '.join(tried) or 'none uploaded'})")

def post_to_instagram(images, caption):
    print("📱 Posting carousel to Instagram...")
    base = "https://graph.instagram.com/v21.0"

    # Upload each slide and create its child container, with per-slide host fallback
    print("📦 Uploading slides & creating child containers...")
    total = len(images)
    child_ids = [_create_child_container(base, path, i + 1, total)
                 for i, path in enumerate(images)]

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

    # Wait for Instagram to process media before publishing
    print("⏳ Waiting 30s for Instagram to process media...")
    time.sleep(30)

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
    if not (NOTION_TOKEN and NOTION_DB_ID):
        print("📝 Notion not configured — skipping log")
        return
    print("📝 Logging to Notion...")
    try:
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
            timeout=15,
        )
        print(f"Notion: {r.status_code}")
        if r.status_code >= 300:
            # Not fatal — dedup no longer depends on Notion. Print body to debug schema.
            print(f"  Notion error body: {r.text[:300]}")
    except Exception as e:
        print(f"  Notion logging failed (non-fatal): {e}")

# ── Main ──────────────────────────────────────────────────────
def main():
    print("🚀 Swimnexar Instagram Bot starting...")

    content   = generate_content()
    print(f"✅ Topic: {content['topic']}")

    waterpolo = _is_waterpolo(content["topic"])
    query     = content.get("pexels_query") or ("water polo" if waterpolo else "swimming")
    cover_img, photo_id = fetch_cover_photo(query, waterpolo, content["topic"])
    images    = create_carousel_images(content, cover_img)
    print(f"✅ Created {len(images)} slides")

    if os.environ.get("DRY_RUN"):
        print("🧪 DRY RUN — slides built, skipping Instagram publish & history update")
        print("🎉 Done (dry run)!")
        return

    post_id = post_to_instagram(images, content["caption"])
    if not post_id:
        log_to_notion(content, None)
        raise SystemExit("❌ Instagram publish failed — post was NOT created (see logs above)")

    print(f"✅ Posted! ID: {post_id}")
    _record_used_topic(content["topic"])
    _record_used_photo(photo_id)
    log_to_notion(content, post_id)
    print("🎉 Done!")

if __name__ == "__main__":
    main()
