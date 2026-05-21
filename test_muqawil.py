from playwright.sync_api import sync_playwright
import time

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://muqawil.org/ar/contractors/20008518/143')
    time.sleep(5)
    with open('profile.html', 'w', encoding='utf-8') as f:
        f.write(page.content())
    browser.close()
