import time
import re
import requests
import sqlite3
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from urllib.parse import quote_plus
import urllib3

urllib3.disable_warnings()

# ─── Patterns ────────────────────────────────────────────────────────────────

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

PHONE_PATTERNS = [
    re.compile(r'\+966[-\s]?[15][0-9][-\s]?[0-9]{3}[-\s]?[0-9]{4}'),
    re.compile(r'00966[-\s]?[15][0-9][-\s]?[0-9]{3}[-\s]?[0-9]{4}'),
    re.compile(r'0[15][0-9][-\s]?[0-9]{3}[-\s]?[0-9]{4}'),
    re.compile(r'\+966[-\s]?[2-9][0-9][-\s]?[0-9]{3}[-\s]?[0-9]{4}'),
    re.compile(r'0[1-9][0-9][-\s]?[0-9]{3}[-\s]?[0-9]{4}'),
]

SOCIAL = {
    'facebook':  re.compile(r'https?://(?:www\.)?facebook\.com/(?!sharer|share\.php|plugins|tr\b|dialog\b|hashtag|watch|video|events|groups|pages/create|marketplace|gaming|help|policies|privacy|legal|ads|business|photo|media|permalink|story\.php|profile\.php\?id=0)([^"\'<>\s?#&]+)', re.I),
    'instagram': re.compile(r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9._]{1,30})/?(?:\s|"|\'|<)', re.I),
    'twitter':   re.compile(r'https?://(?:www\.)?(?:twitter|x)\.com/(?!intent|share|home|search|explore|i/|settings|notifications|messages)([a-zA-Z0-9_]{1,50})/?(?:\s|"|\'|<)', re.I),
    'linkedin':  re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/([^"\'<>\s?#/]+)', re.I),
    'snapchat':  re.compile(r'https?://(?:www\.)?snapchat\.com/add/([^"\'<>\s?#/]+)', re.I),
    'tiktok':    re.compile(r'https?://(?:www\.)?tiktok\.com/@([^"\'<>\s?#/]+)', re.I),
    'youtube':   re.compile(r'https?://(?:www\.)?youtube\.com/(?:channel|c|user|@)([^"\'<>\s?#/]+)', re.I),
    'whatsapp':  re.compile(r'https?://(?:api\.)?wa\.me/(\+?[0-9]{10,14})|https?://(?:api\.)?whatsapp\.com/send\?phone=(\+?[0-9]{10,14})', re.I),
}

EMAIL_BLACKLIST = {'example', 'sentry', 'jquery', 'schema.org', 'w3.org',
                   'openxmlformats', 'apache', 'woocommerce', 'wordpress',
                   'cloudflare', 'google', 'facebook', 'placeholder',
                   'muqawil.org', 'sca.sa'}

CONTACT_PATHS = ['/contact', '/contact-us', '/contacts', '/about',
                 '/about-us', '/اتصل-بنا', '/تواصل-معنا', '/اتصال']


# ─── Helper Functions ─────────────────────────────────────────────────────────

def extract_phones(text):
    results, seen = [], set()
    for pattern in PHONE_PATTERNS:
        for m in pattern.finditer(text):
            clean = re.sub(r'[-\s]', '', m.group())
            if clean not in seen and len(clean) >= 9:
                seen.add(clean)
                results.append(m.group().strip())
    return results


def extract_emails(html):
    found = EMAIL_RE.findall(html)
    clean = []
    for e in found:
        lower = e.lower()
        if not any(b in lower for b in EMAIL_BLACKLIST) and not lower.endswith(('.png', '.jpg', '.gif', '.svg', '.js', '.css')):
            clean.append(e)
    return clean


def extract_social(html):
    result = {}
    for platform, pattern in SOCIAL.items():
        m = pattern.search(html)
        if m:
            full = m.group(0)
            result[platform] = full if full.startswith('http') else 'https://' + full
    return result


# ─── Main Extractor Class ─────────────────────────────────────────────────────

class ContactExtractor:
    def __init__(self, job_state, max_results=20):
        self.state = job_state
        self.max_results = max_results
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/121.0.0.0 Safari/537.36'),
            'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

    def _upd(self, progress=None, message=None):
        if progress is not None:
            self.state['progress'] = min(int(progress), 100)
        if message is not None:
            self.state['message'] = message

    def _check_status(self):
        import time
        while self.state.get('status') == 'paused':
            time.sleep(1)
        if self.state.get('status') == 'stopped_early':
            raise Exception("STOPPED_EARLY")

    def search_router(self, query, location, source, job_id, db_path):
        try:
            try:
                if source == 'muqawil':
                    self._search_muqawil(query, location)
                else:
                    self._search_google(query, location)
            except Exception as e:
                if str(e) == "STOPPED_EARLY":
                    pass # Break out and continue to save
                else:
                    raise e
            
            # --- Post-Processing Filters ---
            if source == 'whatsapp':
                self.state['results'] = [r for r in self.state.get('results', []) if r.get('phone')]
            elif source == 'social':
                self.state['results'] = [r for r in self.state.get('results', []) if r.get('socials')]
            elif source == 'websites':
                self.state['results'] = [r for r in self.state.get('results', []) if r.get('website')]
            # -------------------------------
            
            # Save to DB
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                results_count = len(self.state.get('results', []))
                
                c.execute('''
                    INSERT INTO searches (job_id, query, location, source, date, total_results)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (job_id, query, location, source, date_str, results_count))
                
                for res in self.state.get('results', []):
                    c.execute('''
                        INSERT INTO results (job_id, data)
                        VALUES (?, ?)
                    ''', (job_id, json.dumps(res, ensure_ascii=False)))
                
                conn.commit()
                
        except Exception as ex:
            self.state['status'] = 'error'
            self._upd(message=f'❌ خطأ في الاستخراج أو الحفظ: {ex}')
            import traceback
            traceback.print_exc()

    def _search_google(self, query, location):
        try:
            full_query = f"{query} {location}"
            self._upd(5, 'جاري تشغيل المتصفح...')

            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-infobars',
                        '--window-size=1920,1080',
                    ]
                )
                ctx = browser.new_context(
                    user_agent=self.headers['User-Agent'],
                    viewport={'width': 1920, 'height': 1080},
                    locale='ar-SA',
                    timezone_id='Asia/Riyadh',
                )
                ctx.add_init_script(
                    "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
                )
                page = ctx.new_page()

                # ── Open Google Maps ──────────────────────────────────────
                self._upd(10, 'جاري فتح خرائط جوجل...')
                maps_url = (
                    f"https://www.google.com/maps/search/"
                    f"{quote_plus(full_query)}"
                )
                page.goto(maps_url, wait_until='domcontentloaded', timeout=35000)
                time.sleep(3)

                # Accept consent / cookies
                self._dismiss_consent(page)

                # ── Wait for results feed ─────────────────────────────────
                self._upd(20, 'جاري تحميل قائمة النتائج...')
                try:
                    page.wait_for_selector('div[role="feed"]', timeout=15000)
                except Exception:
                    self._upd(100, '❌ لم يتم تحميل نتائج خرائط جوجل. حاول مرة أخرى.')
                    self.state['status'] = 'error'
                    browser.close()
                    return

                # ── Scroll feed to load more results ─────────────────────
                self._upd(25, 'جاري تحميل المزيد من النتائج...')
                feed = page.locator('div[role="feed"]')
                prev_count = 0
                for _ in range(8):
                    self._check_status()
                    feed.evaluate('el => el.scrollTop += 2000')
                    time.sleep(1.3)
                    cur = page.locator(
                        'div[role="feed"] a[href*="/maps/place/"]'
                    ).count()
                    if cur == prev_count and cur >= self.max_results:
                        break
                    prev_count = cur

                # ── Collect place URLs ────────────────────────────────────
                link_els = page.locator(
                    'div[role="feed"] a[href*="/maps/place/"]'
                ).all()

                place_urls, seen_urls = [], set()
                for el in link_els:
                    self._check_status()
                    href = el.get_attribute('href') or ''
                    if '/maps/place/' not in href:
                        continue
                    if href.startswith('/'):
                        href = 'https://www.google.com' + href
                    # Normalise: strip fragment/query params that vary
                    base = href.split('?')[0]
                    if base not in seen_urls:
                        seen_urls.add(base)
                        place_urls.append(href)
                    if len(place_urls) >= self.max_results:
                        break

                total = len(place_urls)
                if total == 0:
                    self._upd(100, '⚠️ لم يتم العثور على نتائج لهذا البحث.')
                    self.state['status'] = 'done'
                    browser.close()
                    return

                self._upd(30, f'✅ تم العثور على {total} نتيجة - جاري الاستخراج...')

                # ── Visit each place ──────────────────────────────────────
                businesses = []
                for i, url in enumerate(place_urls):
                    self._check_status()
                    prog = 30 + int((i / total) * 45)
                    self._upd(prog, f'جاري استخراج بيانات النتيجة {i + 1} من {total}...')
                    try:
                        page.goto(url, wait_until='domcontentloaded', timeout=20000)
                        time.sleep(2.5)
                        biz = self._extract_place(page)
                        if biz and biz.get('name'):
                            businesses.append(biz)
                    except Exception as ex:
                        print(f"[place {i}] {ex}")
                        continue

                browser.close()

            # ── Scrape websites ───────────────────────────────────────────
            self._upd(75, 'جاري فحص المواقع الإلكترونية...')
            for i, biz in enumerate(businesses):
                self._check_status()
                prog = 75 + int((i / max(len(businesses), 1)) * 22)
                self._upd(prog, f'فحص موقع: {biz.get("name", "")[:30]}...')
                if biz.get('website'):
                    web = self._scrape_website(biz['website'])
                    # Merge: don't overwrite existing data
                    for k, v in web.items():
                        if v and not biz.get(k):
                            biz[k] = v
                self.state['results'].append(biz)

            self.state['status'] = 'done'
            self._upd(100, f'✅ اكتمل! تم استخراج بيانات {len(businesses)} نشاط تجاري')

        except Exception as ex:
            try: browser.close()
            except: pass
            if str(ex) == "STOPPED_EARLY":
                raise ex
            self.state['status'] = 'error'
            self._upd(message=f'❌ حدث خطأ أثناء البحث: {ex}')
            import traceback
            traceback.print_exc()

    def _search_muqawil(self, query, location):
        max_res = self.max_results
        try:
            full_query = f"{query} {location}".strip()
            self._upd(5, 'جاري تشغيل المتصفح للبحث في منصة مقاول...')

            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--window-size=1920,1080']
                )
                ctx = browser.new_context(
                    user_agent=self.headers['User-Agent'],
                    viewport={'width': 1920, 'height': 1080},
                    locale='ar-SA'
                )
                page = ctx.new_page()

                self._upd(10, 'جاري فتح منصة مقاول...')
                search_url = f"https://muqawil.org/ar/contractors?q={quote_plus(full_query)}"
                page.goto(search_url, wait_until='domcontentloaded', timeout=40000)
                time.sleep(4)

                self._upd(20, 'جاري تحميل قائمة المقاولين...')
                
                place_urls = []
                seen_urls = set()
                
                for page_num in range(1, (max_res // 10) + 3):
                    self._check_status()
                    link_els = page.locator('a[href*="/contractors/"]').all()
                    for el in link_els:
                        href = el.get_attribute('href') or ''
                        if '/contractors/' in href and href.count('/') >= 5:
                            base = href.split('?')[0]
                            if base.startswith('/'):
                                base = 'https://muqawil.org' + base
                            if base not in seen_urls:
                                seen_urls.add(base)
                                place_urls.append(base)
                    
                    if len(place_urls) >= max_res:
                        break
                        
                    try:
                        next_btn = page.locator('a.page-link[rel="next"]')
                        if next_btn.is_visible() and next_btn.count() > 0:
                            next_btn.first.click()
                            time.sleep(3)
                        else:
                            break
                    except Exception:
                        break

                place_urls = place_urls[:max_res]
                total = len(place_urls)
                if total == 0:
                    self._upd(100, '⚠️ لم يتم العثور على مقاولين بهذه المواصفات.')
                    self.state['status'] = 'done'
                    browser.close()
                    return

                self._upd(30, f'✅ تم العثور على {total} مقاول - جاري استخراج البيانات...')

                businesses = []
                for i, url in enumerate(place_urls):
                    self._check_status()
                    prog = 30 + int((i / total) * 70)
                    self._upd(prog, f'جاري استخراج بيانات المقاول {i + 1} من {total}...')
                    try:
                        page.goto(url, wait_until='domcontentloaded', timeout=20000)
                        time.sleep(2)
                        
                        biz = {
                            'name': '', 'category': 'مقاول (منصة مقاول)', 'rating': '',
                            'phone': '', 'website': '', 'address': '', 'email': '',
                            'maps_url': url,
                        }
                        
                        try:
                            biz['name'] = page.locator('h1').first.text_content(timeout=3000).strip()
                        except:
                            pass
                        
                        html = page.content()
                        emails = extract_emails(html)
                        if emails:
                            biz['email'] = emails[0]
                            
                        # For Muqawil, the real phone is usually hidden in a javascript block
                        phone_match = re.search(r'رقم الجوال\s*:\s*(\d+)', html)
                        if phone_match:
                            biz['phone'] = phone_match.group(1)
                        else:
                            # Fallback but avoid Muqawil unified number (e.g., 9200)
                            phones = extract_phones(page.inner_text('body'))
                            if phones:
                                for p in phones:
                                    if not p.startswith('9200'):
                                        biz['phone'] = p
                                        break
                                        
                        # Note: Contractors don't have their social media on Muqawil profile pages.
                        # Using extract_social here grabs Muqawil's footer links, so we skip it.
                        # social = extract_social(html)
                        # for k, v in social.items():
                        #     biz[k] = v
                            
                        if biz['name']:
                            businesses.append(biz)
                            self.state['results'].append(biz)
                            
                    except Exception as ex:
                        print(f"[muqawil place {i}] {ex}")
                        continue

                browser.close()
                self.state['status'] = 'done'
                self._upd(100, f'✅ اكتمل! تم استخراج بيانات {len(businesses)} مقاول من منصة مقاول')

        except Exception as ex:
            try: browser.close()
            except: pass
            if str(ex) == "STOPPED_EARLY":
                raise ex
            self.state['status'] = 'error'
            self._upd(message=f'❌ حدث خطأ في منصة مقاول: {ex}')
            import traceback
            traceback.print_exc()

    # ── Dismiss Google consent dialog ────────────────────────────────────────
    def _dismiss_consent(self, page):
        for label in ['قبول الكل', 'Accept all', 'قبول', 'Reject all', 'رفض الكل']:
            try:
                btn = page.get_by_role('button', name=re.compile(label, re.I))
                if btn.is_visible(timeout=2000):
                    btn.click()
                    time.sleep(1)
                    return
            except Exception:
                pass

    # ── Extract data from an open Google Maps place page ─────────────────────
    def _extract_place(self, page):
        biz = {
            'name': '', 'category': '', 'rating': '',
            'phone': '', 'website': '', 'address': '',
            'maps_url': page.url,
        }
        try:
            page.wait_for_load_state('domcontentloaded')
            time.sleep(0.5)

            # --- Name ---
            for sel in ['h1.DUwDvf', 'h1[class*="fontHeadline"]', 'h1']:
                try:
                    t = page.locator(sel).first.text_content(timeout=4000)
                    if t and t.strip():
                        biz['name'] = t.strip()
                        break
                except Exception:
                    continue

            # --- Get visible page text (most reliable for SA phones) ---
            try:
                body_text = page.inner_text('body')
            except Exception:
                body_text = ''

            # --- Phone ---
            phones = extract_phones(body_text)
            if phones:
                biz['phone'] = phones[0]

            # --- Website ---
            website = ''
            # Try #1: data-item-id="authority"
            for sel in [
                '[data-item-id*="authority"] a[href^="http"]',
                'a[data-item-id*="authority"]',
            ]:
                try:
                    el = page.locator(sel).first
                    href = el.get_attribute('href', timeout=2000) or ''
                    if href and 'google.com' not in href and href.startswith('http'):
                        website = href
                        break
                except Exception:
                    pass

            # Try #2: aria-label containing "website" or "موقع"
            if not website:
                try:
                    els = page.locator('a[aria-label]').all()
                    for el in els:
                        aria = (el.get_attribute('aria-label') or '').lower()
                        href = el.get_attribute('href') or ''
                        if ('website' in aria or 'موقع' in aria) and href.startswith('http') and 'google.com' not in href:
                            website = href
                            break
                except Exception:
                    pass

            biz['website'] = website

            # --- Address ---
            for sel in [
                '[data-item-id*="address"] .rogA2c',
                '[data-item-id*="address"]',
                'button[data-tooltip*="address"] + div',
            ]:
                try:
                    t = page.locator(sel).first.text_content(timeout=2000)
                    if t and t.strip() and len(t.strip()) > 5:
                        biz['address'] = t.strip()
                        break
                except Exception:
                    pass

            # Fallback address from aria-label on copy button
            if not biz['address']:
                try:
                    btns = page.locator('button[aria-label]').all()
                    for btn in btns:
                        aria = btn.get_attribute('aria-label') or ''
                        if 'Copy address' in aria or 'عنوان' in aria:
                            # address is usually the text sibling or nearby span
                            parent = btn.locator('xpath=..')
                            t = parent.text_content() or ''
                            t = re.sub(r'\s+', ' ', t).strip()
                            if len(t) > 5:
                                biz['address'] = t
                                break
                except Exception:
                    pass

            # --- Rating ---
            for sel in ['div.F7nice span[aria-hidden="true"]', '.F7nice > span']:
                try:
                    t = page.locator(sel).first.text_content(timeout=1500)
                    if t and re.match(r'[\d.,]+', t.strip()):
                        biz['rating'] = t.strip()
                        break
                except Exception:
                    pass

            # --- Category ---
            for sel in ['button.DkEaL', '[jsaction*="category"]', '.mgr77e']:
                try:
                    t = page.locator(sel).first.text_content(timeout=1500)
                    if t and t.strip():
                        biz['category'] = t.strip()
                        break
                except Exception:
                    pass

        except Exception as ex:
            print(f"[_extract_place] {ex}")

        return biz if biz.get('name') else None

    # ── Scrape a business website for contact info ────────────────────────────
    def _scrape_website(self, url):
        result = {
            'email': '', 'whatsapp': '',
            'facebook': '', 'instagram': '', 'twitter': '',
            'linkedin': '', 'snapchat': '', 'tiktok': '', 'youtube': '',
        }
        if not url:
            return result
        try:
            if not url.startswith('http'):
                url = 'https://' + url

            # Fetch main page
            html = self._fetch(url)
            if html:
                self._parse_html_contacts(html, result)

            # If still missing data, check contact page
            if not result.get('email') or not result.get('phone_web'):
                for path in CONTACT_PATHS:
                    try:
                        contact_url = url.rstrip('/') + path
                        chtml = self._fetch(contact_url, timeout=7)
                        if chtml:
                            self._parse_html_contacts(chtml, result)
                            if result.get('email'):
                                break
                    except Exception:
                        pass

        except Exception as ex:
            print(f"[_scrape_website] {url}: {ex}")

        return result

    def _fetch(self, url, timeout=10):
        try:
            r = requests.get(url, headers=self.headers, timeout=timeout,
                             verify=False, allow_redirects=True)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        return None

    def _parse_html_contacts(self, html, result):
        # Email
        if not result.get('email'):
            emails = extract_emails(html)
            if emails:
                result['email'] = emails[0]

        # Social media
        social = extract_social(html)
        for k, v in social.items():
            if v and not result.get(k):
                result[k] = v

        # WhatsApp from wa.me links
        if not result.get('whatsapp'):
            wa = re.search(
                r'wa\.me/(\+?[0-9]{10,14})|whatsapp\.com/send\?phone=(\+?[0-9]{10,14})',
                html, re.I
            )
            if wa:
                result['whatsapp'] = wa.group(1) or wa.group(2)
