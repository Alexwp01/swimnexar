#!/usr/bin/env python3
"""Weekly blog post generator for Nexar Aquatic Academy."""

import os
import re
import json
import random
import requests
from string import Template
from datetime import datetime, timezone
import anthropic
import replicate

ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]
REPLICATE_KEY  = os.environ["REPLICATE_API_TOKEN"]
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR    = os.path.join(SCRIPT_DIR, '..', 'blog')
POSTS_JSON  = os.path.join(BLOG_DIR, 'posts.json')
IMAGES_DIR  = os.path.join(BLOG_DIR, 'images')

TOPICS = [
    "How to improve freestyle swimming technique for beginners",
    "Water polo positions explained: roles and responsibilities",
    "5 best drills to improve swimming endurance",
    "How to do a flip turn: step-by-step guide for youth swimmers",
    "Water polo fitness: off-season training guide",
    "Breaststroke technique: common mistakes and how to fix them",
    "How young swimmers can prepare for their first competitive meet",
    "Water polo rules explained for new parents",
    "Nutrition tips for young aquatic athletes",
    "Backstroke technique tips for youth swimmers",
    "Mental toughness training for young water polo players",
    "How to choose the right swim goggles",
    "Water polo shooting technique: beginner guide",
    "Effective warm-up routines for young swimmers",
    "College recruiting in water polo: what coaches look for",
    "How swimming builds lifelong fitness and confidence in youth",
    "Butterfly stroke breakdown for youth swimmers",
    "Water polo goalkeeping basics for beginners",
    "How to read the water polo game as a beginner player",
    "Injury prevention tips for young swimmers",
]

POST_TMPL = Template('''\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="$meta_desc">
  <title>$title | Nexar Aquatic Academy</title>
  <link rel="stylesheet" href="../css/style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
  .blog-hero{background:#0d0d0d;padding:120px 0 60px;border-bottom:1px solid #1e1e1e}
  .blog-tag{display:inline-block;background:#d42b2b;color:#fff;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:4px 12px;border-radius:4px;margin-bottom:20px}
  .blog-title{font-size:clamp(28px,5vw,52px);font-weight:800;color:#fff;line-height:1.15;margin-bottom:16px}
  .blog-meta{color:#555;font-size:14px}
  .blog-body{max-width:740px;margin:0 auto;padding:60px 24px 80px}
  .blog-body h2{font-size:26px;font-weight:700;color:#fff;margin:48px 0 16px;border-left:4px solid #d42b2b;padding-left:16px}
  .blog-body h3{font-size:19px;font-weight:600;color:#fff;margin:32px 0 10px}
  .blog-body p{color:#aaa;font-size:17px;line-height:1.8;margin-bottom:20px}
  .blog-body ul,.blog-body ol{color:#aaa;font-size:17px;line-height:1.8;margin-bottom:20px;padding-left:24px}
  .blog-body li{margin-bottom:8px}
  .blog-body strong{color:#e0e0e0}
  .blog-cta{background:#111;border:1px solid #222;border-radius:12px;padding:40px;text-align:center;margin-top:60px}
  .blog-cta h3{color:#fff;font-size:24px;font-weight:700;margin-bottom:12px}
  .blog-cta p{color:#888;margin-bottom:24px}
  .cta-btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
  </style>
</head>
<body>

<header class="header scrolled" id="header">
  <div class="container">
    <a href="../index.html" class="logo">
      <img src="https://swimnexar.com/wp-content/uploads/2025/10/header-title-scaled-129x47.png" alt="Swimnexar">
      <span>Swimnexar</span>
    </a>
    <nav class="nav" id="nav">
      <a href="../index.html" class="nav-link">← Home</a>
      <a href="../waterpolo.html" class="nav-link">Water Polo</a>
      <a href="../swimteam.html" class="nav-link">Swim Team</a>
      <a href="index.html" class="nav-link">Blog</a>
    </nav>
    <div class="header-cta">
      <a href="../waterpolo.html#register" class="btn btn-red btn-sm">Free Trial →</a>
    </div>
    <button class="menu-btn" id="menuBtn" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>

<section class="blog-hero">
  <div class="container">
    <span class="blog-tag">$tag</span>
    <h1 class="blog-title">$title</h1>
    <p class="blog-meta">$date_display &middot; Nexar Aquatic Academy &middot; Wesley Chapel &amp; Land O&apos; Lakes, FL</p>
  </div>
</section>

<main class="blog-body">
  <img src="images/$image_file" alt="$title" style="width:100%;border-radius:12px;margin-bottom:40px;aspect-ratio:16/9;object-fit:cover">
$content

  <div class="blog-cta">
    <h3>Ready to get in the water?</h3>
    <p>First practice is completely FREE &mdash; no commitment needed.</p>
    <div class="cta-btns">
      <a href="../waterpolo.html#register" class="btn btn-red">Water Polo &rarr;</a>
      <a href="../swimteam.html#register" class="btn btn-ghost">Swim Team &rarr;</a>
    </div>
  </div>
</main>

<script src="../js/main.js"></script>
</body>
</html>
''')

INDEX_TMPL = Template('''\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Nexar Aquatic Academy blog — swimming tips, water polo guides, and training advice for youth athletes in Wesley Chapel &amp; Land O&apos; Lakes, FL.">
  <title>Blog | Nexar Aquatic Academy</title>
  <link rel="stylesheet" href="../css/style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
  .blog-index-hero{background:#0d0d0d;padding:120px 0 60px;border-bottom:1px solid #1e1e1e;text-align:center}
  .blog-index-hero h1{font-size:clamp(36px,6vw,64px);font-weight:800;color:#fff;margin-bottom:16px}
  .blog-index-hero p{color:#888;font-size:18px}
  .posts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px;padding:60px 0}
  .post-card{background:#111;border:1px solid #1e1e1e;border-radius:12px;padding:28px;transition:border-color .2s}
  .post-card:hover{border-color:#d42b2b}
  .post-card-tag{display:inline-block;background:#d42b2b22;color:#d42b2b;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:4px;margin-bottom:14px}
  .post-card h2{font-size:19px;font-weight:700;color:#fff;margin-bottom:10px;line-height:1.3}
  .post-card-meta{color:#555;font-size:12px;margin-bottom:10px}
  .post-card p{color:#888;font-size:14px;line-height:1.6;margin-bottom:16px}
  .read-more{color:#d42b2b;font-weight:600;font-size:14px;text-decoration:none}
  .read-more:hover{text-decoration:underline}
  .no-posts{text-align:center;padding:80px 24px;color:#555}
  </style>
</head>
<body>

<header class="header scrolled" id="header">
  <div class="container">
    <a href="../index.html" class="logo">
      <img src="https://swimnexar.com/wp-content/uploads/2025/10/header-title-scaled-129x47.png" alt="Swimnexar">
      <span>Swimnexar</span>
    </a>
    <nav class="nav" id="nav">
      <a href="../index.html" class="nav-link">&larr; Home</a>
      <a href="../waterpolo.html" class="nav-link">Water Polo</a>
      <a href="../swimteam.html" class="nav-link">Swim Team</a>
      <a href="index.html" class="nav-link active">Blog</a>
    </nav>
    <div class="header-cta">
      <a href="../waterpolo.html#register" class="btn btn-red btn-sm">Free Trial &rarr;</a>
    </div>
    <button class="menu-btn" id="menuBtn" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>

<section class="blog-index-hero">
  <div class="container">
    <h1>Aquatic <span style="color:#d42b2b">Academy Blog</span></h1>
    <p>Swimming tips, water polo guides, and training advice for youth athletes.</p>
  </div>
</section>

<section class="section">
  <div class="container">
    $posts_html
  </div>
</section>

<script src="../js/main.js"></script>
</body>
</html>
''')


def load_posts():
    if os.path.exists(POSTS_JSON):
        with open(POSTS_JSON) as f:
            return json.load(f)
    return []


def save_posts(posts):
    with open(POSTS_JSON, 'w') as f:
        json.dump(posts, f, indent=2)


def pick_topic(posts):
    used = {p['topic'] for p in posts}
    available = [t for t in TOPICS if t not in used] or TOPICS
    return random.choice(available)


def generate_post(topic):
    print(f"✍️  Generating: {topic}")
    prompt = f"""You are a content writer for Nexar Aquatic Academy — a youth aquatic sports academy in Wesley Chapel & Land O' Lakes, FL.

Write a blog article about: "{topic}"

Requirements:
- Professional, warm, educational tone — like an experienced coach sharing knowledge
- 550–700 words of article content
- Practical and specific with real actionable advice
- Refer to athletes as "young athletes", "swimmers", or "players" — never "your kids" or "your child"
- Do not address parents directly — share expertise with the community
- Mention Nexar Aquatic Academy naturally 1–2 times only
- No filler phrases like "it's important to" or "make sure to"

Return ONLY valid JSON:
{{
  "title": "Compelling SEO-friendly article title",
  "slug": "url-slug-with-hyphens",
  "tag": "Water Polo" or "Swimming" or "Training" or "Nutrition" or "Recruiting",
  "meta_desc": "SEO description under 155 characters",
  "excerpt": "2 sentence summary for the blog listing page",
  "content": "Full HTML using only <h2> <h3> <p> <ul> <ol> <li> <strong> tags. No <h1>. No inline styles.",
  "image_prompt": "Photorealistic sports photography related to the topic. Professional athletic photography, moody pool lighting or golden hour, cinematic, no text in image"
}}"""

    for attempt in range(3):
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = resp.content[0].text.strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            text = m.group()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"  JSON error (attempt {attempt+1}): {e}")
            if attempt == 2:
                raise


def generate_image(image_prompt, slug):
    print(f"🎨 Generating image...")
    os.makedirs(IMAGES_DIR, exist_ok=True)
    output = replicate.run(
        "black-forest-labs/flux-schnell",
        input={"prompt": image_prompt, "num_outputs": 1, "aspect_ratio": "16:9"}
    )
    url = output[0] if isinstance(output, list) else str(output)
    filename = f"{slug}.jpg"
    r = requests.get(url, timeout=30)
    with open(os.path.join(IMAGES_DIR, filename), 'wb') as f:
        f.write(r.content)
    print(f"✅ Image saved: blog/images/{filename}")
    return filename


def build_post_html(data, date_str, image_file):
    date_display = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
    return POST_TMPL.substitute(
        title=data['title'],
        meta_desc=data['meta_desc'],
        tag=data['tag'],
        date_display=date_display,
        content=data['content'],
        image_file=image_file,
    )


def build_index_html(posts):
    if not posts:
        posts_html = '<div class="no-posts"><p>No posts yet — check back soon!</p></div>'
    else:
        cards = []
        for p in reversed(posts):
            date_display = datetime.strptime(p['date'], '%Y-%m-%d').strftime('%B %d, %Y')
            cards.append(
                f'<div class="post-card">'
                f'<span class="post-card-tag">{p["tag"]}</span>'
                f'<h2>{p["title"]}</h2>'
                f'<p class="post-card-meta">{date_display}</p>'
                f'<p>{p["excerpt"]}</p>'
                f'<a href="{p["filename"]}" class="read-more">Read More &rarr;</a>'
                f'</div>'
            )
        posts_html = '<div class="posts-grid">' + ''.join(cards) + '</div>'
    return INDEX_TMPL.substitute(posts_html=posts_html)


def main():
    os.makedirs(BLOG_DIR, exist_ok=True)
    posts    = load_posts()
    topic    = pick_topic(posts)
    data     = generate_post(topic)
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    filename = f"{date_str}-{data['slug']}.html"
    filepath = os.path.join(BLOG_DIR, filename)

    image_file = generate_image(data['image_prompt'], data['slug'])

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(build_post_html(data, date_str, image_file))
    print(f"✅ Post: blog/{filename}")

    posts.append({
        'topic':    topic,
        'title':    data['title'],
        'slug':     data['slug'],
        'tag':      data['tag'],
        'date':     date_str,
        'excerpt':  data['excerpt'],
        'filename': filename,
    })
    save_posts(posts)

    with open(os.path.join(BLOG_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(build_index_html(posts))
    print("✅ Index updated")


if __name__ == '__main__':
    main()
