import os
import datetime
import requests
import yfinance as yf
import google.generativeai as genai
from bs4 import BeautifulSoup
import base64
import json
import uuid
import argparse
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Constants
CATEGORY_US_STOCKS = "미국주식"
CATEGORY_KR_STOCKS = "한국주식"

def get_wp_headers():
    credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

def get_or_create_category(category_name):
    """Gets category ID by name, or creates it if it doesn't exist."""
    print(f"Checking category: {category_name}...")
    headers = get_wp_headers()
    try:
        search_url = f"{WP_URL}/wp-json/wp/v2/categories?search={category_name}"
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        categories = response.json()
        for cat in categories:
            if cat['name'] == category_name:
                return cat['id']
        print(f"Creating category: {category_name}...")
        create_url = f"{WP_URL}/wp-json/wp/v2/categories"
        data = {"name": category_name}
        response = requests.post(create_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['id']
    except Exception as e:
        print(f"Error managing category {category_name}: {e}")
        return None

def get_or_create_tag(tag_name):
    """Gets tag ID by name, or creates it if it doesn't exist."""
    headers = get_wp_headers()
    try:
        search_url = f"{WP_URL}/wp-json/wp/v2/tags?search={tag_name}"
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        tags = response.json()
        for tag in tags:
            if tag['name'] == tag_name:
                return tag['id']
        create_url = f"{WP_URL}/wp-json/wp/v2/tags"
        data = {"name": tag_name}
        response = requests.post(create_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['id']
    except Exception as e:
        print(f"Error managing tag {tag_name}: {e}")
        return None

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_ticker_data(ticker_symbol):
    """Fetches data for a single ticker."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="5d")
        if hist.empty:
            return None
        last_day = hist.iloc[-1]
        prev_day = hist.iloc[-2] if len(hist) > 1 else last_day
        change = last_day['Close'] - prev_day['Close']
        change_percent = (change / prev_day['Close']) * 100
        return {
            "close": round(last_day['Close'], 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2)
        }
    except Exception:
        return None

def get_market_data(mode):
    """Fetches data based on mode (US or KR)."""
    print(f"Fetching Market Data for {mode}...")
    data = {}
    
    if mode == 'US':
        indices = {
            "Dow Jones": "^DJI",
            "S&P 500": "^GSPC",
            "Nasdaq": "^IXIC"
        }
    elif mode == 'KR':
        indices = {
            "KOSPI": "^KS11",
            "KOSDAQ": "^KQ11"
        }
    else:
        return None

    for name, symbol in indices.items():
        res = get_ticker_data(symbol)
        if res:
            data[name] = res
            
    return data

def get_google_finance_news(query=""):
    """Scrapes top news from Google Finance."""
    print(f"Fetching Google Finance news (Query: {query})...")
    url = "https://www.google.com/finance"
    if query:
        url += f"/quote/{query}" 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        articles = soup.find_all('div', class_='yY3Lee')
        if not articles:
             articles = soup.find_all('div', class_='F2KAFc')
        for article in articles[:5]:
            title_el = article.find('div', class_='Yfwt5')
            if title_el:
                title = title_el.get_text()
                link_el = article.find('a')
                link = link_el['href'] if link_el else "#"
                if link.startswith('./'):
                    link = "https://www.google.com/finance" + link[1:]
                elif link.startswith('/'):
                    link = "https://www.google.com" + link
                news_items.append(f"- {title} ({link})")
        if not news_items:
            return "General market news."
        return "\n".join(news_items)
    except Exception as e:
        print(f"Error fetching news: {e}")
        return "Error fetching news."

def generate_blog_content(mode, market_data, news_data):
    """Generates structured blog content using Gemini."""
    print(f"Generating content for {mode} mode...")
    
    if not GEMINI_API_KEY:
        return None

    model = genai.GenerativeModel('gemini-flash-latest')
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    target_market = "US Stock Market" if mode == 'US' else "Korean Stock Market"
    
    prompt = f"""
    You are a popular financial blogger and SEO expert in Korea. Write a high-quality, engaging blog post for today ({today}) focusing on the **{target_market}**.
    
    Context Data:
    Market Indices: {json.dumps(market_data)}
    News/Events: {news_data}
    
    Requirements:
    1. **SEO Strategy**:
       - **Focus Keyphrase**: Choose a specific, relevant keyphrase (e.g., "{mode} 증시", "{mode} 주식 전망").
       - **Title**: Start with the Focus Keyphrase. Keep it under 60 characters.
       - **Slug**: Include the Focus Keyphrase.
       - **Introduction**: Include the Focus Keyphrase in the first sentence.
       - **Subheadings**: Include the Focus Keyphrase in at least one <h2> or <h3> tag.
       - **Meta Description**: Include the Focus Keyphrase. Length 120-156 characters.
    
    2. **Content Structure**:
       - **Summary**: "💡 3줄 요약" section.
       - **Main Body**: Detailed analysis of the {target_market}.
         - Analyze the indices provided.
         - Discuss key issues/events.
         - Use bullet points and emojis (📈, 📉, 💰).
       - **Links**: 
         - Include at least one **Outbound Link** (e.g., to Yahoo Finance, Google Finance) in the text.
         - Include at least one **Internal Link** (e.g., <a href="{WP_URL}">메인으로 이동</a>).
       - **Image Prompt**:
         - Create a detailed **English description** for an AI image generator representing the {target_market} mood today.
    
    3. **Tone**: Professional yet engaging (Polite Korean, '해요' style).
    
    Output format: JSON
    {{
        "focus_keyphrase": "Selected Keyphrase",
        "title": "Title starting with Keyphrase",
        "content": "HTML Content (do NOT include the main image here)",
        "meta_description": "Meta description with keyphrase",
        "tags": ["tag1", "tag2", "tag3"],
        "image_prompt_en": "Detailed English image prompt here",
        "summary_points": "3 bullet points summary (string with newlines)"
    }}
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generating content: {e}")
        return None

# --- Elementor Helper Functions ---
def el_id(): return str(uuid.uuid4())[:8]

def el_section(elements, is_inner=False, background_color=None):
    settings = {}
    if background_color:
        settings["background_color"] = background_color
        settings["padding"] = {"unit": "px", "top": "30", "right": "20", "bottom": "30", "left": "20", "isLinked": False}
    
    return {
        "id": el_id(),
        "elType": "section",
        "isInner": is_inner,
        "settings": settings,
        "elements": elements
    }

def el_column(elements, width=100):
    return {
        "id": el_id(),
        "elType": "column",
        "isInner": False,
        "settings": {
            "_column_size": width,
            # Mobile width 100% is default in Elementor if not specified, 
            # but explicit settings can ensure it. 
            # Elementor JSON structure for responsive controls is complex.
            # We rely on default stacking behavior for mobile.
        },
        "elements": elements
    }

def el_widget(widget_type, settings):
    return {
        "id": el_id(),
        "elType": "widget",
        "isInner": False,
        "widgetType": widget_type,
        "settings": settings
    }

def el_heading(text, tag="h2", align="left"):
    return el_widget("heading", {
        "title": text, 
        "header_size": tag,
        "align": align
    })

def el_text(content):
    return el_widget("text-editor", {"editor": content})

def el_divider():
    return el_widget("divider", {"gap": {"unit": "px", "size": 30}})

def el_card(title, value, change, change_pct):
    color = "#ff0000" if change >= 0 else "#0000ff" # KR Style
    sign = "+" if change >= 0 else ""
    bg_color = "#f9f9f9"
    
    # Simple, high-contrast card for mobile readability
    content = f"""
    <div style="text-align:center; padding: 15px; background-color: {bg_color}; border-radius: 12px; margin-bottom: 10px;">
        <p style="margin:0; font-size: 14px; color:#555; font-weight: 500;">{title}</p>
        <h3 style="margin:5px 0; font-size: 24px; color:#222; font-weight: 700;">{value}</h3>
        <p style="margin:0; font-size: 16px; color:{color}; font-weight:bold;">{sign}{change} ({sign}{change_pct}%)</p>
    </div>
    """
    return el_widget("html", {"html": content})

def create_elementor_post(mode, content_data, market_data):
    """Builds the UX-optimized Elementor JSON structure."""
    
    today = datetime.date.today().strftime('%Y-%m-%d')
    update_time = datetime.datetime.now().strftime('%H:%M')
    market_name = "미국 증시" if mode == 'US' else "한국 증시"
    flag = "🇺🇸" if mode == 'US' else "🇰🇷"
    
    # 1. Header Section (Clean, centered, clear date)
    header_section = el_section([
        el_column([
            el_heading(f"{flag} {today} {market_name}", "h1", "center"),
            el_text(f"<p style='text-align:center; color:#666; margin-top:-10px;'>🕒 {update_time} 업데이트 | 3분 요약</p>"),
            el_divider()
        ])
    ])
    
    # 2. Key Summary Section (Highlighted Box)
    # Background color #f0f4f8 (Light Blue/Gray) to stand out
    summary_content = f"""
    <div style="font-size: 1.1em; line-height: 1.6;">
        {content_data.get('summary_points', '')}
    </div>
    """
    summary_section = el_section([
        el_column([
            el_heading("🚀 오늘의 핵심 3줄", "h3"),
            el_text(summary_content)
        ])
    ], background_color="#f0f4f8")
    
    # 3. Market Cards (Grid)
    cards = []
    if market_data:
        # Desktop: 3 columns (33%), Mobile: Stacks automatically
        width = 33 if len(market_data) >= 3 else (50 if len(market_data) == 2 else 100)
        for name, data in market_data.items():
            cards.append(el_column([el_card(name, data['close'], data['change'], data['change_percent'])], width=width))
            
    cards_section = el_section(cards, is_inner=True)
    
    market_section = el_section([
        el_column([
            el_divider(),
            el_heading(f"📊 {market_name} 지수", "h3"),
            cards_section
        ])
    ])
    
    # 4. Main Content (Readable Text)
    # Add some spacing and typography tweaks via inline styles in the content generation or here
    content_section = el_section([
        el_column([
            el_divider(),
            el_heading("🔥 상세 시장 분석", "h3"),
            el_text(content_data.get('content', ''))
        ])
    ])
    
    # 5. Footer
    footer_section = el_section([
        el_column([
            el_divider(),
            el_text("<p style='text-align:center; font-size:12px; color:#999;'>본 정보는 투자 참고용이며, 투자의 책임은 본인에게 있습니다.</p>")
        ])
    ])
    
    full_structure = [header_section, summary_section, market_section, content_section, footer_section]
    return json.dumps(full_structure)

def create_elementor_json(html_content):
    """Fallback simple wrapper if needed."""
    # Not used in new logic but kept for safety
    return json.dumps([]) 

def upload_image_to_wordpress(image_prompt, alt_text):
    """Generates an image via Pollinations.ai, uploads to WP, and returns ID and URL."""
    print(f"Generating and uploading image for prompt: {image_prompt}...")
    encoded_prompt = requests.utils.quote(image_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&nologo=true"
    
    try:
        img_response = requests.get(image_url)
        img_response.raise_for_status()
        img_data = img_response.content
        
        filename = f"stock_news_{uuid.uuid4()}.jpg"
        headers = get_wp_headers()
        headers["Content-Type"] = "image/jpeg"
        headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        upload_url = f"{WP_URL}/wp-json/wp/v2/media"
        response = requests.post(upload_url, headers=headers, data=img_data)
        response.raise_for_status()
        
        result = response.json()
        media_id = result['id']
        source_url = result['source_url']
        
        update_url = f"{WP_URL}/wp-json/wp/v2/media/{media_id}"
        meta_headers = get_wp_headers()
        meta_data = {"alt_text": alt_text, "description": alt_text, "caption": alt_text}
        requests.post(update_url, headers=meta_headers, json=meta_data)
        
        print(f"Image uploaded successfully: ID {media_id}")
        return media_id, source_url
    except Exception as e:
        print(f"Error uploading image: {e}")
        return None, None

def post_to_wordpress(post_data_dict, elementor_json, category_id):
    """Posts content to WordPress."""
    print("Posting to WordPress...")
    
    if not WP_URL or not WP_USERNAME or not WP_APP_PASSWORD:
        return False

    headers = get_wp_headers()
    
    tag_ids = []
    if 'tags' in post_data_dict:
        for tag_name in post_data_dict['tags']:
            tid = get_or_create_tag(tag_name)
            if tid: tag_ids.append(tid)
            
    # Handle Image
    featured_media_id = None
    image_html = ""
    if 'image_prompt_en' in post_data_dict:
        focus_kw = post_data_dict.get('focus_keyphrase', 'Stock Market')
        mid, murl = upload_image_to_wordpress(post_data_dict['image_prompt_en'], focus_kw)
        if mid:
            featured_media_id = mid
            image_html = f'<img src="{murl}" alt="{focus_kw}" class="wp-image-{mid}" style="width:100%; height:auto; border-radius:10px; margin-bottom:20px;" />'

    # Construct Full Content (Fallback & SEO)
    full_content = image_html + "\n\n" + post_data_dict.get('content', '')

    wp_post_data = {
        "title": post_data_dict.get('title'),
        "content": full_content, # Populated for visibility
        "excerpt": post_data_dict.get('meta_description'),
        "status": "publish",
        "categories": [category_id],
        "featured_media": featured_media_id,
        "tags": tag_ids,
        "meta": {
            "_elementor_edit_mode": "builder",
            "_elementor_template_type": "wp-post",
            "_elementor_data": elementor_json,
            "_yoast_wpseo_focuskw": post_data_dict.get('focus_keyphrase', ''),
            "_yoast_wpseo_metadesc": post_data_dict.get('meta_description', ''),
            "_yoast_wpseo_title": post_data_dict.get('title', '')
        }
    }
    
    try:
        api_url = f"{WP_URL}/wp-json/wp/v2/posts"
        response = requests.post(api_url, headers=headers, json=wp_post_data)
        response.raise_for_status()
        print(f"Successfully posted: {response.json().get('link')}")
        return True
    except Exception as e:
        print(f"Error posting to WordPress: {e}")
        if 'response' in locals() and response:
            print(f"Response: {response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description="WordPress Stock Automation")
    parser.add_argument("--mode", type=str, choices=['US', 'KR'], help="Mode: US or KR")
    args = parser.parse_args()
    
    # Determine Mode
    mode = args.mode
    if not mode:
        # Auto-detect based on hour if not provided
        hour = datetime.datetime.now().hour
        if hour < 12:
            mode = 'US' # Morning -> US Market (closed)
        else:
            mode = 'KR' # Afternoon -> KR Market (closed)
    
    print(f"Starting Automation in [{mode}] mode at {datetime.datetime.now()}")
    
    # 1. Fetch Data
    market_data = get_market_data(mode)
    news_data = get_google_finance_news() # Always get some news context
    
    # 2. Generate Content
    content_data = generate_blog_content(mode, market_data, news_data)
    
    if content_data:
        # 3. Build Elementor Layout
        elementor_json = create_elementor_post(mode, content_data, market_data)
        
        # 4. Determine Category
        cat_id = get_or_create_category(CATEGORY_US_STOCKS if mode == 'US' else CATEGORY_KR_STOCKS)
        
        # 5. Post
        post_to_wordpress(content_data, elementor_json, cat_id)
    else:
        print("Failed to generate content.")

if __name__ == "__main__":
    main()
