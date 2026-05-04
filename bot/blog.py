#!/usr/bin/env python3
"""Weekly blog post generator — real news + Pexels photos."""

import os
import re
import json
import random
import requests
import feedparser
from string import Template
from datetime import datetime, timezone
import anthropic

ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
PEXELS_KEY    = os.environ["PEXELS_API_KEY"]
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR   = os.path.join(SCRIPT_DIR, '..', 'blog')
POSTS_JSON = os.path.join(BLOG_DIR, 'posts.json')
IMAGES_DIR = os.path.join(BLOG_DIR, 'images')

NEWS_FEEDS = [
    "https://news.google.com/rss/search?q=water+polo+youth&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=youth+swimming+competition&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=water+polo+USA&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=youth+swim+team+Florida&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=swimming+technique+kids&hl=en-US&gl=US&ceid=US:en",
]

POST_TMPL = Template('''\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="$meta_desc">
  <title>$title | Nexar Aquatic Academy</title>
  <link rel="canonical" href="https://swimnexar.com/blog/$filename">
  <meta property="og:title"       content="$title">
  <meta property="og:description" content="$meta_desc">
  <meta property="og:image"       content="https://swimnexar.com/blog/images/$image_file">
  <meta property="og:type"        content="article">
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
  .blog-cover{width:100%;border-radius:12px;margin-bottom:40px;aspect-ratio:16/9;object-fit:cover}
  .photo-credit{color:#444;font-size:11px;text-align:right;margin-top:-32px;margin-bottom:40px}
  .photo-credit a{color:#555}
  .blog-body h2{font-size:26px;font-weight:700;color:#fff;margin:48px 0 16px;border-left:4px solid #d42b2b;padding-left:16px}
  .blog-body h3{font-size:19px;font-weight:600;color:#fff;margin:32px 0 10px}
  .blog-body p{color:#aaa;font-size:17px;line-height:1.8;margin-bottom:20px}
  .blog-body ul,.blog-body ol{color:#aaa;font-size:17px;line-height:1.8;margin-bottom:20px;padding-left:24px}
  .blog-body li{margin-bottom:8px}
  .blog-body strong{color:#e0e0e0}
  .blog-source{background:#111;border:1px solid #1e1e1e;border-radius:8px;padding:16px 20px;margin-bottom:48px;font-size:14px;color:#666}
  .blog-source a{color:#888}
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
      <a href="../index.html" class="nav-link">&larr; Home</a>
      <a href="../waterpolo.html" class="nav-link">Water Polo</a>
      <a href="../swimteam.html" class="nav-link">Swim Team</a>
      <a href="index.html" class="nav-link">Blog</a>
    </nav>
    <div class="header-cta">
      <a href="../waterpolo.html#register" class="btn btn-red btn-sm">Free Trial &rarr;</a>
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
    <p class="blog-meta">$date_display &middot; Nexar Aquatic Academy</p>
  </div>
</section>

<main class="blog-body">
  <img src="images/$image_file" alt="$title" class="blog-cover">
  <p class="photo-credit">Photo: <a href="$photo_url" target="_blank" rel="noopener">$photo_credit</a> via Pexels</p>

  <div class="blog-source">
    &ldquo;$news_title&rdquo; &mdash; <a href="$news_url" target="_blank" rel="noopener noreferrer">Read original article</a>
  </div>

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
  <meta name="description" content="Nexar Aquatic Academy blog — latest water polo and swimming news, tips, and guides for youth athletes in Wesley Chapel &amp; Land O&apos; Lakes, FL.">
  <title>Blog | Nexar Aquatic Academy</title>
  <link rel="canonical" href="https://swimnexar.com/blog/index.html">
  <link rel="stylesheet" href="../css/style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
  .blog-index-hero{background:#0d0d0d;padding:120px 0 60px;border-bottom:1px solid #1e1e1e;text-align:center}
  .blog-index-hero h1{font-size:clamp(36px,6vw,64px);font-weight:800;color:#fff;margin-bottom:16px}
  .blog-index-hero p{color:#888;font-size:18px}
  .posts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:24px;padding:60px 0}
  .post-card{background:#111;border:1px solid #1e1e1e;border-radius:12px;overflow:hidden;transition:border-color .2s}
  .post-card:hover{border-color:#d42b2b}
  .post-card-img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
  .post-card-body{padding:24px}
  .post-card-tag{display:inline-block;background:#d42b2b22;color:#d42b2b;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:4px;margin-bottom:12px}
  .post-card h2{font-size:18px;font-weight:700;color:#fff;margin-bottom:8px;line-height:1.3}
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
    <p>Latest water polo &amp; swimming news, tips, and training guides.</p>
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


def fetch_news():
    """Grab articles from Google News RSS feeds."""
    articles = []
    feed_url = random.choice(NEWS_FEEDS)
    print(f"📰 Fetching news: {feed_url}")
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:10]:
        articles.append({
            'title':   entry.get('title', ''),
            'summary': entry.get('summary', entry.get('description', '')),
            'url':     entry.get('link', ''),
        })
    return articles


def fetch_pexels_photo(query):
    """Search Pexels for a photo matching the query."""
    print(f"📷 Searching Pexels: {query}")
    r = requests.get(
        'https://api.pexels.com/v1/search',
        headers={'Authorization': PEXELS_KEY},
        params={'query': query, 'per_page': 10, 'orientation': 'landscape'},
        timeout=15
    )
    results = r.json().get('photos', [])
    if not results:
        # Fallback to generic query
        r = requests.get(
            'https://api.pexels.com/v1/search',
            headers={'Authorization': PEXELS_KEY},
            params={'query': 'swimming pool sport', 'per_page': 10, 'orientation': 'landscape'},
            timeout=15
        )
        results = r.json().get('photos', [])
    photo = random.choice(results)
    return {
        'url':         photo['src']['large2x'],
        'page_url':    photo['url'],
        'photographer': photo['photographer'],
    }


def download_photo(photo_info, slug):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    filename = f"{slug}.jpg"
    r = requests.get(photo_info['url'], timeout=30)
    with open(os.path.join(IMAGES_DIR, filename), 'wb') as f:
        f.write(r.content)
    print(f"✅ Photo saved: blog/images/{filename}")
    return filename


def generate_post(article):
    print(f"✍️  Writing article based on: {article['title'][:60]}...")
    # Clean HTML from summary
    summary = re.sub(r'<[^>]+>', '', article['summary'])[:800]
    prompt = f"""You are a content writer for Nexar Aquatic Academy — a youth aquatic sports academy in Wesley Chapel & Land O' Lakes, FL.

A real news article was published:
Title: {article['title']}
Summary: {summary}
URL: {article['url']}

Write a blog post for our academy inspired by this news. Connect it to youth aquatic sports — water polo or swimming.
Make it relevant to parents and young athletes in the Tampa Bay area.

Requirements:
- 500–650 words
- Professional, warm, educational tone
- Complete grammatically correct sentences — no fragments
- Refer to athletes as "young athletes", "swimmers", or "players"
- Mention Nexar Aquatic Academy naturally once or twice
- Include a Pexels search query (2-4 words) for a relevant photo
- Local angle: Wesley Chapel, Land O' Lakes, Tampa Bay area when natural

Return ONLY valid JSON:
{{
  "title": "Compelling blog post title",
  "slug": "url-slug-with-hyphens",
  "tag": "Water Polo" or "Swimming" or "Training" or "Nutrition" or "Recruiting",
  "meta_desc": "SEO description under 155 characters",
  "excerpt": "2 sentence summary for blog listing",
  "pexels_query": "2-4 word photo search query",
  "content": "Full HTML using only <h2> <h3> <p> <ul> <ol> <li> <strong> tags. No <h1>. No inline styles."
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


def build_post_html(data, date_str, image_file, photo_info, article):
    date_display = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
    filename = f"{date_str}-{data['slug']}.html"
    return POST_TMPL.substitute(
        title=data['title'],
        meta_desc=data['meta_desc'],
        tag=data['tag'],
        date_display=date_display,
        filename=filename,
        image_file=image_file,
        photo_url=photo_info['page_url'],
        photo_credit=photo_info['photographer'],
        news_title=article['title'],
        news_url=article['url'],
        content=data['content'],
    )


def build_index_html(posts):
    if not posts:
        posts_html = '<div class="no-posts"><p>No posts yet — check back soon!</p></div>'
    else:
        cards = []
        for p in reversed(posts):
            date_display = datetime.strptime(p['date'], '%Y-%m-%d').strftime('%B %d, %Y')
            img_tag = f'<img src="images/{p["image_file"]}" alt="{p["title"]}" class="post-card-img">' if p.get('image_file') else ''
            cards.append(
                f'<div class="post-card">'
                f'{img_tag}'
                f'<div class="post-card-body">'
                f'<span class="post-card-tag">{p["tag"]}</span>'
                f'<h2>{p["title"]}</h2>'
                f'<p class="post-card-meta">{date_display}</p>'
                f'<p>{p["excerpt"]}</p>'
                f'<a href="{p["filename"]}" class="read-more">Read More &rarr;</a>'
                f'</div></div>'
            )
        posts_html = '<div class="posts-grid">' + ''.join(cards) + '</div>'
    return INDEX_TMPL.substitute(posts_html=posts_html)


def main():
    os.makedirs(BLOG_DIR, exist_ok=True)
    posts   = load_posts()
    articles = fetch_news()
    if not articles:
        print("❌ No articles found")
        return

    article  = random.choice(articles[:5])
    data     = generate_post(article)
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    filename = f"{date_str}-{data['slug']}.html"

    photo_info = fetch_pexels_photo(data.get('pexels_query', 'water polo swimming'))
    image_file = download_photo(photo_info, data['slug'])

    filepath = os.path.join(BLOG_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(build_post_html(data, date_str, image_file, photo_info, article))
    print(f"✅ Post: blog/{filename}")

    posts.append({
        'title':      data['title'],
        'slug':       data['slug'],
        'tag':        data['tag'],
        'date':       date_str,
        'excerpt':    data['excerpt'],
        'filename':   filename,
        'image_file': image_file,
    })
    save_posts(posts)

    with open(os.path.join(BLOG_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(build_index_html(posts))
    print("✅ Index updated")


if __name__ == '__main__':
    main()
