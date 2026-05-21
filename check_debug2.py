import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
html = open('debug2.html', encoding='utf-8').read()
print('EMAILS:', set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)))
print('SOCIAL:', set(re.findall(r'https?://(?:www\.)?(?:facebook|instagram|twitter|x|linkedin|snapchat|tiktok|youtube)\.com/[^\"\'<>\s?#]+', html)))
