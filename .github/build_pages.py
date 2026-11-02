#!/usr/bin/env python3
# OraNW — يبني صفحات الذهب لكل دولة، وأسعار العملات، ومواقيت الصلاة، واختبار السرعة، وخريطة الموقع
# يعمل بعد archive.py في كل تشغيل للروبوت، فتبقى الأرقام داخل الصفحات حديثة ومقروءة لمحركات البحث
import json, os, sys, datetime, urllib.request, urllib.parse, html
sys.path.insert(0, os.path.dirname(__file__))
from site_common import page

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OZ = 31.1035
UA = 'Mozilla/5.0 (OraNW page builder; +https://oranw.com)'
NOW = datetime.datetime.now(datetime.timezone.utc)
MONTHS = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
DAYS = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
PEG = {'SAR': 3.75, 'AED': 3.6725, 'QAR': 3.64, 'BHD': 0.376, 'OMR': 0.3845, 'JOD': 0.709, 'USD': 1.0}

def esc(s): return html.escape(str(s), quote=True)
def ar_date(iso, with_day=False):
    d = datetime.date.fromisoformat(iso)
    return (DAYS[d.weekday()] + ' ' if with_day else '') + '%d %s %d' % (d.day, MONTHS[d.month - 1], d.year)
def fmt(v, dec=2):
    if v is None: return '—'
    return format(v, ',.%df' % dec)
def dec_for(v): return 0 if v >= 1000 else (2 if v >= 1 else 4)
def get_json(url, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))
def write(name, content):
    with open(os.path.join(ROOT, name), 'w', encoding='utf-8') as f: f.write(content)

# ---------------- البيانات ----------------
archive = json.load(open(os.path.join(ROOT, 'archive.json'), encoding='utf-8'))
archive = [e for e in archive if e.get('d')]
latest = archive[-1]
LIVE_FX = None
if not latest.get('fx'):
    try: LIVE_FX = get_json('https://open.er-api.com/v6/latest/USD').get('rates')
    except Exception: LIVE_FX = None

def rate(e, code):
    if code == 'USD': return 1.0
    fx = e.get('fx') or {}
    if fx.get(code): return float(fx[code])
    if e is latest and LIVE_FX and LIVE_FX.get(code): return float(LIVE_FX[code])
    return PEG.get(code)

def last_with(key, n=None):
    xs = [e for e in archive if e.get(key) is not None]
    return xs if n is None else xs[-n:]

GOLD_E = last_with('gold')
G_NOW = GOLD_E[-1] if GOLD_E else None
G_PREV = GOLD_E[-2] if len(GOLD_E) > 1 else None
STAMP = (G_NOW['d'] + (' ' + G_NOW['ts'] if G_NOW.get('ts') else '')) if G_NOW else ''

def faq_schema(qas):
    return '<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qas]
    }, ensure_ascii=False) + '</script>'
def faq_html(qas):
    return '<h2>أسئلة شائعة</h2>' + ''.join('<h3>%s</h3><p>%s</p>' % (esc(q), esc(a)) for q, a in qas)

EXTRA_CSS = '''
.big{font-size:clamp(30px,8vw,42px);font-weight:800;line-height:1.3}
.up{color:var(--up)}.down{color:var(--down)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.chips a{font-size:14px;padding:6px 12px;border:1px solid var(--bd);border-radius:9px;text-decoration:none;color:var(--fg2)}
.calc{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}
.calc input,.calc select{padding:9px 12px;border:1px solid var(--bd);border-radius:10px;background:transparent;color:var(--fg);font-family:inherit;font-size:16px}
.calc input{width:130px}
.res{font-size:22px;font-weight:800;margin-top:6px}
.hl td{font-weight:700;color:var(--fg)}
'''

def chg_html(a, b):
    if a is None or b is None or not b: return ''
    p = (a - b) / b * 100
    cls = 'up' if p >= 0 else 'down'
    return '<span class="%s num">%s%.2f%%</span>' % (cls, '▲ +' if p >= 0 else '▼ ', abs(p)) if abs(p) >= 0.005 else '<span class="num">دون تغيير</span>'

# ======================= 1) الذهب لكل دولة =======================
COUNTRIES = [
    # slug, name, in_name, code, cur_name, main karat, karats, note
    ('saudi-arabia', 'السعودية', 'في السعودية', 'SAR', 'ريال سعودي', 21, [24, 22, 21, 18], 'عيار 21 هو الأكثر انتشاراً في المشغولات بالسعودية، وعيار 24 للسبائك. الريال مربوط بالدولار عند 3.75، لذلك يتبع سعر الذهب بالريال السعر العالمي مباشرة.'),
    ('uae', 'الإمارات', 'في الإمارات', 'AED', 'درهم إماراتي', 22, [24, 22, 21, 18], 'في الإمارات يُسعَّر الذهب عادة بعيارات 24 و22 و21 و18، وسوق الذهب في دبي من أكبر الأسواق في العالم. الدرهم مربوط بالدولار عند 3.6725.'),
    ('kuwait', 'الكويت', 'في الكويت', 'KWD', 'دينار كويتي', 22, [24, 22, 21, 18], 'الدينار الكويتي مرتبط بسلة عملات، لذلك يتغير سعر الذهب بالدينار مع الذهب العالمي ومع حركة سعر الصرف معاً.'),
    ('qatar', 'قطر', 'في قطر', 'QAR', 'ريال قطري', 22, [24, 22, 21, 18], 'الريال القطري مربوط بالدولار عند 3.64، وعيارا 22 و21 هما الأكثر طلباً في المشغولات.'),
    ('bahrain', 'البحرين', 'في البحرين', 'BHD', 'دينار بحريني', 22, [24, 22, 21, 18], 'الدينار البحريني مربوط بالدولار عند 0.376، ويُباع الذهب غالباً بعيار 22 و21.'),
    ('oman', 'عُمان', 'في عُمان', 'OMR', 'ريال عُماني', 22, [24, 22, 21, 18], 'الريال العماني مربوط بالدولار عند 0.3845، وعيار 22 شائع في الحلي العمانية.'),
    ('egypt', 'مصر', 'في مصر', 'EGP', 'جنيه مصري', 21, [24, 21, 18], 'عيار 21 هو الأكثر تداولاً في مصر. لاحظ أن أسعار محلات الصاغة في مصر قد تختلف عن السعر المحسوب هنا من السعر العالمي وسعر الصرف المرجعي، بسبب ظروف السوق المحلية والمصنعية.'),
    ('jordan', 'الأردن', 'في الأردن', 'JOD', 'دينار أردني', 21, [24, 21, 18], 'الدينار الأردني مربوط بالدولار عند 0.709 تقريباً، وعيار 21 هو الأكثر انتشاراً في السوق الأردني.'),
    ('morocco', 'المغرب', 'في المغرب', 'MAD', 'درهم مغربي', 18, [24, 22, 18], 'عيار 18 هو الأكثر شيوعاً في المجوهرات بالمغرب. الدرهم المغربي مرتبط بسلة من اليورو والدولار.'),
    ('iraq', 'العراق', 'في العراق', 'IQD', 'دينار عراقي', 21, [24, 21, 18], 'في العراق يُسعَّر الذهب غالباً بالمثقال (5 غرامات) وبالدولار أو الدينار. السعر هنا محسوب بسعر الصرف الرسمي، وقد يختلف عن سعر السوق الموازية.'),
]
PURITY = {24: 0.999, 22: 22 / 24, 21: 21 / 24, 18: 18 / 24}

def gram(e, code, k):
    r = rate(e, code)
    if e.get('gold') is None or r is None: return None
    return e['gold'] / OZ * PURITY[k] * r

GOLD_PAGES = []
for slug, name, in_name, code, cur, main_k, karats, note in COUNTRIES:
    path = '/gold-' + slug
    fname = 'gold-' + slug + '.html'
    GOLD_PAGES.append((path, name))
    if not G_NOW: continue
    r_now = rate(G_NOW, code)
    dec = 0 if code == 'IQD' else 2
    g_main = gram(G_NOW, code, main_k)
    rows = ''
    for k in karats:
        v = gram(G_NOW, code, k); pv = gram(G_PREV, code, k) if G_PREV else None
        rows += '<tr%s><td>عيار %d</td><td class="num">%s %s</td><td>%s</td></tr>' % (' class="hl"' if k == main_k else '', k, fmt(v, dec), code, chg_html(v, pv))
    oz_local = G_NOW['gold'] * r_now if r_now else None
    rows += '<tr><td>الأونصة (31.1 غ) عيار 24</td><td class="num">%s %s</td><td></td></tr>' % (fmt(oz_local, dec), code)
    if code == 'IQD':
        rows += '<tr><td>المثقال (5 غ) عيار 21</td><td class="num">%s IQD</td><td></td></tr>' % fmt(gram(G_NOW, code, 21) * 5 if gram(G_NOW, code, 21) else None, 0)
    hist = ''
    for e in [x for x in GOLD_E[-14:] if rate(x, code)][::-1][:10]:
        hist += '<tr><td class="num"><a href="/day/%s">%s</a></td><td class="num">%s</td></tr>' % (e['d'], e['d'], fmt(gram(e, code, main_k), dec))
    others = ''.join('<a href="/gold-%s">%s</a>' % (s2, n2) for s2, n2, *_ in COUNTRIES if s2 != slug)
    gm = fmt(g_main, dec)
    qas = [
        ('كم سعر غرام الذهب عيار %d اليوم %s؟' % (main_k, in_name), 'سعر غرام الذهب عيار %d %s حسب آخر تحديث (%s UTC) هو %s %s تقريباً، وهو سعر الخام المحسوب من السعر العالمي دون المصنعية.' % (main_k, in_name, STAMP, gm, cur)),
        ('هل السعر يشمل المصنعية؟', 'لا. السعر المعروض هو قيمة الذهب الخام فقط. محلات الصاغة تضيف المصنعية وأحياناً ضريبة القيمة المضافة، فيكون سعر المشغولات أعلى.'),
        ('كيف يُحسب سعر الغرام %s؟' % in_name, 'نقسم سعر الأونصة العالمي بالدولار على 31.1035 غرام، ثم نضربه في نسبة نقاء العيار، ثم في سعر صرف %s مقابل الدولار.' % cur),
        ('كم مرة يتحدث السعر؟', 'تتحدث هذه الصفحة تلقائياً 4 مرات يومياً من أرشيف OraNW، ويظهر وقت آخر تحديث أعلى الصفحة.'),
    ]
    body = '''<div class="crumbs"><a href="/gold">سعر الذهب</a> › %(name)s</div>
<h1>سعر الذهب اليوم %(in_name)s</h1>
<p class="lead">%(date)s — آخر تحديث %(stamp)s UTC. أسعار غرام الذهب بالـ%(cur)s لكل عيار.</p>
<div class="card">
  <div class="note">غرام الذهب عيار %(k)d %(in_name)s</div>
  <div class="big num">%(gm)s <span style="font-size:18px">%(code)s</span></div>
  <div>%(chg)s <span class="note">مقارنة بـ %(prev)s</span></div>
</div>
<table><tr><th>العيار</th><th>سعر الغرام</th><th>التغيّر اليومي</th></tr>%(rows)s</table>
<h2>احسب قيمة ذهبك</h2>
<div class="card">
  <div class="calc"><input id="g" type="number" inputmode="decimal" value="10" min="0" step="0.1" class="num" aria-label="الوزن بالغرام"> غرام عيار
  <select id="k">%(kopts)s</select></div>
  <div class="res num" id="res">—</div>
  <p class="note">القيمة التقريبية للذهب الخام دون مصنعية.</p>
</div>
<h2>عن سعر الذهب %(in_name)s</h2>
<p>%(note)s</p>
<p>السعر العالمي للأونصة الآن <strong class="num">$%(oz)s</strong>، وسعر صرف الدولار المستخدم في الحساب <strong class="num">%(rate)s %(code)s</strong>.</p>
<h2>سعر غرام عيار %(k)d في الأيام الأخيرة</h2>
<table><tr><th>التاريخ</th><th>عيار %(k)d (%(code)s)</th></tr>%(hist)s</table>
%(faq)s
<h2>سعر الذهب في دول أخرى</h2>
<div class="chips">%(others)s</div>
<p class="note">الأسعار للاطلاع فقط وليست نصيحة استثمارية. البيانات من أرشيف OraNW اليومي.</p>
''' % dict(name=name, in_name=in_name, date=ar_date(G_NOW['d'], True), stamp=STAMP, cur=cur, k=main_k, gm=gm, code=code,
           chg=chg_html(g_main, gram(G_PREV, code, main_k) if G_PREV else None), prev=G_PREV['d'] if G_PREV else '',
           rows=rows, kopts=''.join('<option value="%d"%s>%d</option>' % (k, ' selected' if k == main_k else '', k) for k in karats),
           note=note, oz=fmt(G_NOW['gold']), rate=fmt(r_now, 4 if r_now < 1 else 2), hist=hist, faq=faq_html(qas), others=others)
    js = '''<script>
var OZP=%s, R=%s, P={24:0.999,22:22/24,21:21/24,18:0.75}, D=%d, C="%s";
function calc(){ var g=parseFloat(document.getElementById("g").value)||0, k=+document.getElementById("k").value;
  document.getElementById("res").textContent=(OZP/31.1035*P[k]*R*g).toLocaleString("en-US",{maximumFractionDigits:D})+" "+C; }
document.getElementById("g").oninput=calc; document.getElementById("k").onchange=calc; calc();
</script>''' % (G_NOW['gold'], r_now, dec, code)
    title = 'سعر الذهب اليوم %s — غرام عيار %d و24 و18 بالـ%s | OraNW' % (in_name, main_k, cur)
    desc = 'سعر الذهب اليوم %s: غرام عيار %d بـ%s %s. أسعار كل العيارات بالـ%s تتحدث 4 مرات يومياً، مع حاسبة وسجل الأيام الأخيرة.' % (in_name, main_k, gm, code, cur)
    write(fname, page(path, esc(title), esc(desc), body, extra_css=EXTRA_CSS, schema=faq_schema(qas)).replace('</body>', js + '\n</body>'))

# ======================= 2) أسعار العملات =======================
CUR = {'USD': ('الدولار الأمريكي', 'دولار'), 'EUR': ('اليورو', 'يورو'), 'SAR': ('الريال السعودي', 'ريال سعودي'), 'AED': ('الدرهم الإماراتي', 'درهم إماراتي'),
       'KWD': ('الدينار الكويتي', 'دينار كويتي'), 'EGP': ('الجنيه المصري', 'جنيه مصري'), 'JOD': ('الدينار الأردني', 'دينار أردني'),
       'IQD': ('الدينار العراقي', 'دينار عراقي'), 'MAD': ('الدرهم المغربي', 'درهم مغربي'), 'DZD': ('الدينار الجزائري', 'دينار جزائري'),
       'TRY': ('الليرة التركية', 'ليرة تركية'), 'QAR': ('الريال القطري', 'ريال قطري')}
PAIRS = [('USD', 'EGP'), ('USD', 'SAR'), ('SAR', 'EGP'), ('USD', 'AED'), ('AED', 'EGP'), ('KWD', 'EGP'),
         ('USD', 'JOD'), ('USD', 'IQD'), ('USD', 'MAD'), ('USD', 'DZD'), ('USD', 'TRY'), ('EUR', 'EGP')]
PARALLEL = {'EGP', 'IQD', 'DZD'}

def cross(e, a, b):
    ra, rb = rate(e, a), rate(e, b)
    return rb / ra if ra and rb else None

CUR_PAGES = []
for a, b in PAIRS:
    slug = '%s-to-%s' % (a.lower(), b.lower())
    path, fname = '/' + slug, slug + '.html'
    an, ash = CUR[a]; bn, bsh = CUR[b]
    CUR_PAGES.append((path, '%s مقابل %s' % (an, bn)))
    v = cross(latest, a, b)
    prev_e = next((e for e in reversed(archive[:-1]) if cross(e, a, b)), None)
    pv = cross(prev_e, a, b) if prev_e else None
    d = dec_for(v) if v else 2
    amounts = [1, 5, 10, 20, 50, 100, 500, 1000]
    tbl = ''.join('<tr><td class="num">%s %s</td><td class="num">%s %s</td></tr>' % (fmt(x, 0), a, fmt(x * v, 2 if x * v < 1000 else 0), b) for x in amounts) if v else ''
    inv = ''.join('<tr><td class="num">%s %s</td><td class="num">%s %s</td></tr>' % (fmt(x, 0), b, fmt(x / v, 4 if x / v < 1 else 2), a) for x in amounts) if v else ''
    hist_rows = ''.join('<tr><td class="num">%s</td><td class="num">%s</td></tr>' % (e['d'], fmt(cross(e, a, b), d)) for e in [x for x in archive if cross(x, a, b)][-10:][::-1])
    note = 'هذا هو السعر الرسمي المرجعي. في %s قد يختلف سعر السوق الموازية عنه، فتأكد من سعر البنك أو شركة الصرافة قبل التحويل.' % bn if b in PARALLEL else 'السعر مرجعي متوسط بين الشراء والبيع، وسعر البنك أو الصرافة الفعلي يتضمن هامشاً بسيطاً.'
    others = ''.join('<a href="/%s-to-%s">%s ← %s</a>' % (x.lower(), y.lower(), x, y) for x, y in PAIRS if (x, y) != (a, b))
    qas = [
        ('كم سعر %s مقابل %s اليوم؟' % (an, bn), '1 %s يساوي %s %s حسب آخر تحديث في OraNW.' % (ash, fmt(v, d), bsh)),
        ('كم يساوي 100 %s بالـ%s؟' % (ash, bsh), '100 %s تساوي تقريباً %s %s.' % (ash, fmt(100 * v, 2) if v else '—', bsh)),
        ('هل هذا سعر البنك؟', 'لا، هو سعر مرجعي من مصادر بيانات أسعار الصرف الدولية، والبنوك وشركات الصرافة تضيف هامشاً بين سعري الشراء والبيع.'),
    ]
    body = '''<div class="crumbs"><a href="/currency">أسعار العملات</a> › %(a)s/%(b)s</div>
<h1>سعر %(an)s مقابل %(bn)s اليوم</h1>
<p class="lead">%(date)s — آخر تحديث %(ts)s UTC.</p>
<div class="card">
  <div class="note">1 %(ash)s =</div>
  <div class="big num">%(v)s <span style="font-size:18px">%(b)s</span></div>
  <div>%(chg)s</div>
</div>
<h2>محوّل %(ash)s إلى %(bsh)s</h2>
<div class="card">
  <div class="calc"><input id="amt" type="number" inputmode="decimal" value="100" class="num" aria-label="المبلغ"> <span id="from">%(a)s</span>
  <button id="sw" type="button" style="padding:8px 12px;border:1px solid var(--bd);border-radius:10px;background:transparent;color:var(--fg2);cursor:pointer;font-family:inherit">⇄ عكس</button></div>
  <div class="res num" id="res">—</div>
</div>
<h2>جدول التحويل</h2>
<table><tr><th>%(an)s</th><th>%(bn)s</th></tr>%(tbl)s</table>
<table><tr><th>%(bn)s</th><th>%(an)s</th></tr>%(inv)s</table>
%(hist)s
<p>%(note)s</p>
%(faq)s
<h2>عملات أخرى</h2>
<div class="chips">%(others)s</div>
''' % dict(a=a, b=b, an=an, bn=bn, ash=ash, bsh=bsh, date=ar_date(latest['d'], True), ts=latest['d'] + ' ' + latest.get('ts', ''),
           v=fmt(v, d), chg=(chg_html(v, pv) + ' <span class="note">مقارنة بـ %s</span>' % prev_e['d']) if pv else '',
           tbl=tbl, inv=inv, hist=('<h2>السعر في الأيام الأخيرة</h2><table><tr><th>التاريخ</th><th>1 %s بالـ%s</th></tr>%s</table>' % (a, b, hist_rows)) if hist_rows.count('<tr>') > 1 else '',
           note=note, faq=faq_html(qas), others=others)
    js = '''<script>
var R=%s, A="%s", B="%s", flip=false;
function calc(){ var x=parseFloat(document.getElementById("amt").value)||0, v=flip?x/R:x*R;
  document.getElementById("from").textContent=flip?B:A;
  document.getElementById("res").textContent="= "+v.toLocaleString("en-US",{maximumFractionDigits:v<1?4:2})+" "+(flip?A:B); }
document.getElementById("amt").oninput=calc; document.getElementById("sw").onclick=function(){flip=!flip;calc();}; calc();
fetch("https://open.er-api.com/v6/latest/"+A).then(function(r){return r.json();}).then(function(j){ if(j&&j.rates&&j.rates[B]){ R=j.rates[B]; calc(); } }).catch(function(){});
</script>''' % (v or 0, a, b)
    title = 'سعر %s مقابل %s اليوم — %s إلى %s | OraNW' % (an, bn, a, b)
    desc = 'سعر %s مقابل %s اليوم: 1 %s = %s %s. محوّل مباشر وجدول تحويل وسجل الأيام الأخيرة، يتحدث 4 مرات يومياً.' % (an, bn, ash, fmt(v, d), bsh)
    write(fname, page(path, esc(title), esc(desc), body, extra_css=EXTRA_CSS, schema=faq_schema(qas)).replace('</body>', js + '\n</body>'))

# hub
rows = ''.join('<tr><td><a href="/%s-to-%s">%s ← %s</a></td><td class="num">%s</td></tr>' % (a.lower(), b.lower(), a, b, fmt(cross(latest, a, b), dec_for(cross(latest, a, b) or 1))) for a, b in PAIRS)
write('currency.html', page('/currency', 'أسعار العملات اليوم مقابل الدولار والجنيه والريال | OraNW',
    'أسعار صرف العملات العربية اليوم: الدولار مقابل الجنيه المصري والريال السعودي والدرهم والدينار، تتحدث 4 مرات يومياً مع محوّل لكل عملة.',
    '<h1>أسعار العملات اليوم</h1><p class="lead">آخر تحديث %s UTC. اختر العملة لترى المحوّل وجدول التحويل والسجل.</p><table><tr><th>الزوج</th><th>السعر</th></tr>%s</table><p class="note">أسعار مرجعية من مصادر بيانات الصرف الدولية. للحسابات اليومية استخدم أيضاً <a href="/#ccAmt">محوّل العملات في الرئيسية</a>.</p>' % (latest['d'] + ' ' + latest.get('ts', ''), rows),
    extra_css=EXTRA_CSS))

# ======================= 3) مواقيت الصلاة =======================
CITIES = [
    ('makkah', 'مكة المكرمة', 'Makkah', 'SA', 4), ('madinah', 'المدينة المنورة', 'Medina', 'SA', 4), ('riyadh', 'الرياض', 'Riyadh', 'SA', 4),
    ('jeddah', 'جدة', 'Jeddah', 'SA', 4), ('dammam', 'الدمام', 'Dammam', 'SA', 4), ('dubai', 'دبي', 'Dubai', 'AE', 16),
    ('abu-dhabi', 'أبوظبي', 'Abu Dhabi', 'AE', 16), ('kuwait', 'الكويت', 'Kuwait City', 'KW', 9), ('doha', 'الدوحة', 'Doha', 'QA', 10),
    ('manama', 'المنامة', 'Manama', 'BH', 8), ('muscat', 'مسقط', 'Muscat', 'OM', 8), ('cairo', 'القاهرة', 'Cairo', 'EG', 5),
    ('alexandria', 'الإسكندرية', 'Alexandria', 'EG', 5), ('amman', 'عمّان', 'Amman', 'JO', 23), ('baghdad', 'بغداد', 'Baghdad', 'IQ', 3),
    ('casablanca', 'الدار البيضاء', 'Casablanca', 'MA', 21), ('algiers', 'الجزائر', 'Algiers', 'DZ', 19),
]
METHOD = {4: 'أم القرى', 16: 'الهيئة العامة للشؤون الإسلامية بدبي', 9: 'وزارة الأوقاف الكويتية', 10: 'قطر', 8: 'منطقة الخليج',
          5: 'الهيئة المصرية العامة للمساحة', 23: 'وزارة الأوقاف الأردنية', 3: 'رابطة العالم الإسلامي', 21: 'وزارة الأوقاف المغربية', 19: 'وزارة الشؤون الدينية الجزائرية'}
PNAMES = [('Fajr', 'الفجر'), ('Sunrise', 'الشروق'), ('Dhuhr', 'الظهر'), ('Asr', 'العصر'), ('Maghrib', 'المغرب'), ('Isha', 'العشاء')]
CACHE_F = os.path.join(os.path.dirname(__file__), 'prayer_cache.json')
try: PCACHE = json.load(open(CACHE_F, encoding='utf-8'))
except Exception: PCACHE = {}

PRAYER_PAGES = []
for slug, ar, en, cc, method in CITIES:
    path, fname = '/prayer-times-' + slug, 'prayer-times-' + slug + '.html'
    PRAYER_PAGES.append((path, ar))
    data = None
    try:
        j = get_json('https://api.aladhan.com/v1/timingsByCity?city=%s&country=%s&method=%d' % (urllib.parse.quote(en), cc, method))
        data = j.get('data'); PCACHE[slug] = data
    except Exception:
        data = PCACHE.get(slug)
    t = (data or {}).get('timings', {})
    hij = (data or {}).get('date', {}).get('hijri', {})
    greg = (data or {}).get('date', {}).get('gregorian', {}).get('date', '')
    hij_txt = '%s %s %s هـ' % (hij.get('day', ''), hij.get('month', {}).get('ar', ''), hij.get('year', '')) if hij else ''
    rows = ''.join('<tr><td>%s</td><td class="num" id="t-%s">%s</td></tr>' % (n, k, esc(t.get(k, '—')[:5])) for k, n in PNAMES)
    others = ''.join('<a href="/prayer-times-%s">%s</a>' % (s2, a2) for s2, a2, *_ in CITIES if s2 != slug)
    qas = [
        ('متى أذان الفجر في %s اليوم؟' % ar, 'أذان الفجر في %s اليوم الساعة %s حسب تقويم %s.' % (ar, t.get('Fajr', '—')[:5], METHOD.get(method, ''))),
        ('متى أذان المغرب في %s اليوم؟' % ar, 'أذان المغرب في %s اليوم الساعة %s.' % (ar, t.get('Maghrib', '—')[:5])),
        ('ما طريقة الحساب المستخدمة؟', 'نستخدم طريقة %s، وهي المعتمدة في هذه المنطقة. قد تختلف المواعيد دقيقة أو دقيقتين عن تقويم مسجدك المحلي.' % METHOD.get(method, '')),
    ]
    body = '''<div class="crumbs"><a href="/prayer-times">مواقيت الصلاة</a> › %(ar)s</div>
<h1>مواقيت الصلاة في %(ar)s اليوم</h1>
<p class="lead"><span class="num">%(greg)s</span> · %(hij)s</p>
<div class="card"><div class="note">الصلاة القادمة</div><div class="big" id="next">—</div><div class="num" id="left"></div></div>
<table><tr><th>الصلاة</th><th>الوقت</th></tr>%(rows)s</table>
<p class="note">طريقة الحساب: %(method)s. المواعيد بالتوقيت المحلي لمدينة %(ar)s.</p>
%(faq)s
<h2>مواقيت الصلاة في مدن أخرى</h2>
<div class="chips">%(others)s</div>
''' % dict(ar=ar, greg=esc(greg), hij=esc(hij_txt), rows=rows, method=METHOD.get(method, ''), faq=faq_html(qas), others=others)
    tz = (data or {}).get('meta', {}).get('timezone', 'UTC')
    js = '''<script>
var CITY="%s", CC="%s", M=%d, TZ="%s", N=%s, T=%s;
function nowTZ(){ var s=new Date().toLocaleString("en-US",{timeZone:TZ,hour12:false}); return new Date(s); }
function tick(){ if(!T) return; var n=nowTZ(), mins=n.getHours()*60+n.getMinutes()+n.getSeconds()/60, best=null;
  ["Fajr","Dhuhr","Asr","Maghrib","Isha"].forEach(function(k){ var p=(T[k]||"").slice(0,5).split(":"); var m=+p[0]*60+ +p[1]; if(best===null && m>mins) best=[k,m]; });
  if(!best){ var p=(T.Fajr||"0:0").slice(0,5).split(":"); best=["Fajr",+p[0]*60+ +p[1]+1440]; }
  var d=best[1]-mins, h=Math.floor(d/60), mm=Math.floor(d%%60), ss=Math.floor((d*60)%%60);
  document.getElementById("next").textContent=N[best[0]]+" "+(T[best[0]]||"").slice(0,5);
  document.getElementById("left").textContent="بعد "+h+" س "+mm+" د "+ss+" ث"; }
fetch("https://api.aladhan.com/v1/timingsByCity?city="+encodeURIComponent(CITY)+"&country="+CC+"&method="+M).then(function(r){return r.json();}).then(function(j){
  if(j&&j.data&&j.data.timings){ T=j.data.timings; Object.keys(N).forEach(function(k){ var el=document.getElementById("t-"+k); if(el&&T[k]) el.textContent=T[k].slice(0,5); }); if(j.data.meta) TZ=j.data.meta.timezone; tick(); } }).catch(function(){});
tick(); setInterval(tick,1000);
</script>''' % (en, cc, method, tz, json.dumps({k: n for k, n in PNAMES}, ensure_ascii=False), json.dumps(t) if t else 'null')
    title = 'مواقيت الصلاة في %s اليوم — أذان الفجر والظهر والمغرب | OraNW' % ar
    desc = 'مواقيت الصلاة في %s اليوم%s: الفجر %s، الظهر %s، العصر %s، المغرب %s، العشاء %s. مع العد التنازلي للصلاة القادمة.' % (ar, (' ' + hij_txt) if hij_txt else '', t.get('Fajr', '—')[:5], t.get('Dhuhr', '—')[:5], t.get('Asr', '—')[:5], t.get('Maghrib', '—')[:5], t.get('Isha', '—')[:5])
    write(fname, page(path, esc(title), esc(desc), body, extra_css=EXTRA_CSS, schema=faq_schema(qas)).replace('</body>', js + '\n</body>'))
try: json.dump(PCACHE, open(CACHE_F, 'w', encoding='utf-8'), ensure_ascii=False)
except Exception: pass

write('prayer-times.html', page('/prayer-times', 'مواقيت الصلاة اليوم في المدن العربية | OraNW',
    'مواقيت الصلاة اليوم في مكة والمدينة والرياض وجدة ودبي والكويت والدوحة والقاهرة وعمّان وبغداد والدار البيضاء والجزائر، مع العد التنازلي للصلاة القادمة.',
    '<h1>مواقيت الصلاة اليوم</h1><p class="lead">اختر مدينتك لترى مواعيد الأذان اليوم والوقت المتبقي للصلاة القادمة.</p><div class="chips">%s</div><p>مواقيت صلاة موقعك الحالي تظهر أيضاً في <a href="/">الصفحة الرئيسية</a> حسب موقع جهازك.</p>' % ''.join('<a href="%s">%s</a>' % p for p in PRAYER_PAGES),
    extra_css=EXTRA_CSS))

# ======================= ربط صفحة الذهب الرئيسية بالدول =======================
gp = os.path.join(ROOT, 'gold.html')
if os.path.exists(gp):
    s = open(gp, encoding='utf-8').read()
    block = '<!--countries--><h2>سعر الذهب في الدول العربية</h2><div class="chips">' + ''.join('<a href="%s">%s</a>' % p for p in GOLD_PAGES) + '</div><!--/countries-->'
    if '<!--countries-->' in s:
        s = s[:s.index('<!--countries-->')] + block + s[s.index('<!--/countries-->') + len('<!--/countries-->'):]
    else:
        s = s.replace('<h2>السجل اليومي', block + '\n<h2>السجل اليومي', 1)
    if '.chips{' not in s:
        s = s.replace('</style>', '.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.chips a{font-size:14px;padding:6px 12px;border:1px solid var(--bd);border-radius:9px;text-decoration:none;color:var(--fg2)}</style>', 1)
    open(gp, 'w', encoding='utf-8').write(s)

# ======================= خريطة الموقع =======================
STATIC = [('/', '1.0', 'hourly'), ('/en/', '0.8', 'hourly'), ('/tools', '0.9', 'weekly'), ('/speed-test', '0.9', 'weekly'), ('/archive', '0.8', 'daily'),
          ('/gold', '0.9', 'daily'), ('/bitcoin', '0.8', 'daily'), ('/oil', '0.8', 'daily'), ('/currency', '0.8', 'daily'), ('/prayer-times', '0.8', 'daily'),
          ('/guides', '0.6', 'monthly'), ('/what-is-dns', '0.6', 'monthly'), ('/what-is-my-ip', '0.6', 'monthly'), ('/ping-jitter', '0.6', 'monthly'),
          ('/what-are-ports', '0.6', 'monthly'), ('/about', '0.4', 'yearly'), ('/contact', '0.4', 'yearly'), ('/privacy', '0.3', 'yearly')]
today = NOW.strftime('%Y-%m-%d')
urls = [(p, pr, cf) for p, pr, cf in STATIC] + [(p, '0.8', 'daily') for p, _ in GOLD_PAGES + CUR_PAGES + PRAYER_PAGES]
x = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for p, pr, cf in urls:
    lm = today if cf in ('hourly', 'daily') else '2026-11-02'
    x += '  <url><loc>https://oranw.com%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>\n' % (p, lm, cf, pr)
x += '</urlset>\n'
write('sitemap.xml', x)
print('pages built:', len(GOLD_PAGES), 'gold,', len(CUR_PAGES), 'currency,', len(PRAYER_PAGES), 'prayer')
