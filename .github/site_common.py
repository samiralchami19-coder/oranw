# Shared head / nav / footer for OraNW static pages
SITE = "https://oranw.com"
ADS = '''<meta name="google-adsense-account" content="ca-pub-6507978376685782">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6507978376685782" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-04H2SF0KVS"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-04H2SF0KVS');</script>'''

CSS = ''':root{--bg:#ffffff;--fg:#111111;--fg2:#444444;--fg3:#777777;--fg4:#aaaaaa;--bd:#e5e5e5;--mut:#f2f2f2;--up:#0a7d3b;--down:#c0392b;--warn:#b8860b}
@media (prefers-color-scheme:dark){:root{--bg:#111111;--fg:#f2f2f2;--fg2:#c8c8c8;--fg3:#8a8a8a;--fg4:#5a5a5a;--bd:#2c2c2c;--mut:#1d1d1d;--up:#3ecf7a;--down:#ff6b5e;--warn:#e6b93d}}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Kufi Arabic","Helvetica Neue",Arial,sans-serif;background:var(--bg);color:var(--fg);max-width:720px;margin:0 auto;padding:16px 16px 40px;line-height:1.9;font-size:16px}
a{color:inherit}
.num{font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:18px;font-size:14px}
.topbar .brand{font-weight:800;text-decoration:none;font-size:17px}
.topbar .links{display:flex;gap:14px;flex-wrap:wrap}
.topbar .links a{color:var(--fg3);text-decoration:none}
.topbar .links a:hover{color:var(--fg)}
h1{font-size:26px;line-height:1.5;margin-bottom:6px}
.lead{color:var(--fg3);font-size:15px;margin-bottom:22px}
h2{font-size:20px;margin:28px 0 8px;line-height:1.5}
h3{font-size:17px;margin:20px 0 6px}
p,li{color:var(--fg2);margin-bottom:10px}
ul,ol{padding-inline-start:24px;margin-bottom:10px}
strong{color:var(--fg)}
code{direction:ltr;unicode-bidi:embed;background:var(--mut);border:1px solid var(--bd);border-radius:6px;padding:1px 6px;font-size:14px;font-family:ui-monospace,Menlo,Consolas,monospace}
.card{border:1px solid var(--bd);border-radius:14px;padding:16px;margin:14px 0}
.cta{display:inline-block;margin-top:6px;padding:10px 18px;border-radius:10px;background:var(--fg);color:var(--bg);text-decoration:none;font-weight:700;font-size:15px}
table{width:100%;border-collapse:collapse;font-size:14px;margin:8px 0}
th,td{padding:8px;text-align:start;border-bottom:1px solid var(--bd)}
th{color:var(--fg3);font-size:12px;font-weight:600}
.note{font-size:12px;color:var(--fg4);margin-top:6px}
.upd{font-size:12px;color:var(--fg4);margin-bottom:18px}
.sitefoot{margin-top:40px;padding-top:18px;border-top:1px solid var(--bd);font-size:13px;color:var(--fg4);text-align:center;line-height:2.2}
.sitefoot a{color:var(--fg3);text-decoration:none;margin:0 6px;white-space:nowrap}
.sitefoot a:hover{color:var(--fg)}
.crumbs{font-size:13px;color:var(--fg4);margin-bottom:6px}
.crumbs a{color:var(--fg3);text-decoration:none}
'''

NAV = '''<header class="topbar"><a class="brand" href="/">OraNW</a>
<nav class="links"><a href="/gold">الذهب</a> <a href="/currency">العملات</a> <a href="/prayer-times">الصلاة</a> <a href="/tools">الأدوات</a></nav></header>'''

FOOT = '''<footer class="sitefoot">
<div><a href="/">الرئيسية</a> <a href="/tools">أدوات الشبكة</a> <a href="/archive">أرشيف الكوكب</a> <a href="/gold">سعر الذهب</a> <a href="/bitcoin">سعر البيتكوين</a> <a href="/oil">سعر النفط</a> <a href="/currency">أسعار العملات</a> <a href="/prayer-times">مواقيت الصلاة</a> <a href="/speed-test">اختبار سرعة النت</a> <a href="/guides">الشروحات</a></div>
<div><a href="/about">من نحن</a> <a href="/contact">اتصل بنا</a> <a href="/privacy">سياسة الخصوصية</a> <a href="/en/">English</a></div>
<div>OraNW © 2026</div>
</footer>'''


def page(path, title, desc, body, extra_head="", extra_css="", schema="", og_title=None, lang="ar"):
    url = SITE + path
    d = "rtl" if lang == "ar" else "ltr"
    return f'''<!DOCTYPE html>
<html lang="{lang}" dir="{d}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#111111">
<meta property="og:type" content="website">
<meta property="og:site_name" content="OraNW">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{og_title or title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{SITE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}/og.png">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icon.png">
{schema}
{ADS}
<style>{CSS}{extra_css}</style>
{extra_head}
</head>
<body>
{NAV}
<main>
{body}
</main>
{FOOT}
</body>
</html>
'''


def article_schema(path, headline, desc):
    return f'''<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"{headline}","description":"{desc}","inLanguage":"ar","mainEntityOfPage":"{SITE}{path}","author":{{"@type":"Organization","name":"OraNW"}},"publisher":{{"@type":"Organization","name":"OraNW","logo":{{"@type":"ImageObject","url":"{SITE}/icon.png"}}}},"datePublished":"2026-11-02","dateModified":"2026-11-02","image":"{SITE}/og.png"}}</script>'''
