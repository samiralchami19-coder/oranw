#!/usr/bin/env python3
# OraNW — صفحات التاريخ الهجري، حاسبة الزكاة، وعدّادات رمضان والعيدين
# يعمل بعد build_pages.py في كل تشغيل للروبوت
import json, os, sys, datetime, subprocess, html, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from site_common import page

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RIYADH = datetime.timezone(datetime.timedelta(hours=3))
TODAY = datetime.datetime.now(RIYADH).date()
OZ = 31.1035
G_MONTHS = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
H_MONTHS = ['محرم', 'صفر', 'ربيع الأول', 'ربيع الآخر', 'جمادى الأولى', 'جمادى الآخرة', 'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة']
WDAYS = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
# تواريخ أم القرى (محسوبة من تقويم أم القرى)، وقد تختلف يوماً حسب رؤية الهلال
EVENTS = {
    'ramadan': [('1448', '2027-02-08'), ('1449', '2028-01-28'), ('1450', '2029-01-16'), ('1451', '2030-01-05')],
    'fitr':    [('1448', '2027-03-09'), ('1449', '2028-02-26'), ('1450', '2029-02-14'), ('1451', '2030-02-04')],
    'adha':    [('1448', '2027-05-16'), ('1449', '2028-05-05'), ('1450', '2029-04-24'), ('1451', '2030-04-13')],
}

def esc(s): return html.escape(str(s), quote=True)
def gdate(d): return '%d %s %d' % (d.day, G_MONTHS[d.month - 1], d.year)
def write(name, content):
    with open(os.path.join(ROOT, name), 'w', encoding='utf-8') as f: f.write(content)
def fmt(v, dec=2): return '—' if v is None else format(v, ',.%df' % dec)

def hijri_of(dates):
    """يحوّل قائمة تواريخ ميلادية إلى هجري (أم القرى) عبر Intl في Node، ثم aladhan احتياطاً."""
    try:
        js = ("const f=new Intl.DateTimeFormat('en-u-ca-islamic-umalqura',{day:'numeric',month:'numeric',year:'numeric'});"
              "const ds=%s;console.log(JSON.stringify(ds.map(s=>{const p=f.formatToParts(new Date(s+'T12:00:00Z'));"
              "const g=t=>+p.find(x=>x.type===t).value;return [g('year'),g('month'),g('day')];})));") % json.dumps([d.isoformat() for d in dates])
        out = subprocess.run(['node', '-e', js], capture_output=True, text=True, timeout=30).stdout
        return [tuple(x) for x in json.loads(out)]
    except Exception:
        res = []
        for d in dates:
            try:
                req = urllib.request.Request('https://api.aladhan.com/v1/gToH/%s?calendarMethod=UAQ' % d.strftime('%d-%m-%Y'), headers={'User-Agent': 'OraNW builder'})
                h = json.loads(urllib.request.urlopen(req, timeout=15).read())['data']['hijri']
                res.append((int(h['year']), int(h['month']['number']), int(h['day'])))
            except Exception:
                res.append(None)
        return res

def hstr(h): return '%d %s %d هـ' % (h[2], H_MONTHS[h[1] - 1], h[0]) if h else ''

CSS = '''
.big{font-size:clamp(32px,8vw,46px);font-weight:800;line-height:1.25}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.chips a{font-size:14px;padding:6px 12px;border:1px solid var(--bd);border-radius:10px;text-decoration:none;color:var(--fg2);background:var(--bg)}
.calc{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}
.calc input,.calc select{padding:9px 12px;border:1px solid var(--bd);border-radius:10px;background:var(--bg);color:var(--fg);font-family:inherit;font-size:16px}
.calc label{font-size:14px;color:var(--fg3);display:block;margin-bottom:4px}
.res{font-size:22px;font-weight:800;margin-top:8px;color:var(--navy)}
@media (prefers-color-scheme:dark){.res{color:#F5C451}}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.grid2 input,.grid2 select{width:100%;padding:9px 12px;border:1px solid var(--bd);border-radius:10px;background:var(--bg);color:var(--fg);font:inherit;font-size:16px}
.grid2 label{display:block;font-size:13.5px;color:var(--fg3);margin-bottom:4px}
.cd{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0 6px;text-align:center}
.cd div{background:var(--navy);color:#fff;border-radius:14px;padding:14px 6px}
.cd b{display:block;font-size:clamp(26px,7vw,40px);font-variant-numeric:tabular-nums;line-height:1.1}
.cd span{font-size:12px;opacity:.75}
.hl td{font-weight:700;color:var(--fg)}
@media (max-width:520px){.grid2{grid-template-columns:1fr}}
'''

def faq_schema(qas):
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qas]}, ensure_ascii=False) + '</script>'
def faq_html(qas): return '<h2>أسئلة شائعة</h2>' + ''.join('<h3>%s</h3><p>%s</p>' % (esc(q), esc(a)) for q, a in qas)

NEW_PATHS = []

# ======================= 1) التاريخ الهجري =======================
month_days = [TODAY + datetime.timedelta(days=i) for i in range(-31, 32)]
hs = hijri_of(month_days)
H_TODAY = hs[31]
rows = ''
if H_TODAY:
    for d, h in zip(month_days, hs):
        if h and h[0] == H_TODAY[0] and h[1] == H_TODAY[1]:
            rows += '<tr%s><td class="num">%d %s</td><td>%s</td><td class="num">%s</td></tr>' % (
                ' class="hl"' if d == TODAY else '', h[2], H_MONTHS[h[1] - 1], WDAYS[d.weekday()], gdate(d))
next_events = []
for key, name in [('ramadan', 'رمضان'), ('fitr', 'عيد الفطر'), ('adha', 'عيد الأضحى')]:
    y, d = next((y, datetime.date.fromisoformat(d)) for y, d in EVENTS[key] if datetime.date.fromisoformat(d) >= TODAY)
    next_events.append((key, name, y, d, (d - TODAY).days))
qas = [
    ('ما هو التاريخ الهجري اليوم؟', 'اليوم %s %s الموافق %s م حسب تقويم أم القرى.' % (WDAYS[TODAY.weekday()], hstr(H_TODAY), gdate(TODAY))),
    ('ما هو تقويم أم القرى؟', 'هو التقويم الهجري الرسمي في المملكة العربية السعودية، ويُحسب فلكياً. قد يختلف عن رؤية الهلال في بعض الدول بيوم واحد.'),
    ('كم عدد أيام الشهر الهجري؟', 'الشهر الهجري 29 أو 30 يوماً، والسنة الهجرية 354 أو 355 يوماً، أي أقصر من السنة الميلادية بنحو 11 يوماً.'),
]
body = '''<h1>التاريخ الهجري اليوم</h1>
<p class="lead">حسب تقويم أم القرى، ويتحدث تلقائياً حسب تاريخ جهازك.</p>
<div class="card">
  <div class="note" id="hWd">%(wd)s</div>
  <div class="big" id="hNow">%(h)s</div>
  <div class="num" id="gNow" style="color:var(--fg3)">الموافق %(g)s م</div>
</div>
<h2>تحويل التاريخ</h2>
<div class="card">
  <div class="calc"><label style="width:100%%">من ميلادي إلى هجري</label><input type="date" id="gIn" class="num" value="%(iso)s" aria-label="تاريخ ميلادي"></div>
  <div class="res" id="gOut">—</div>
</div>
<div class="card">
  <label style="font-size:14px;color:var(--fg3)">من هجري إلى ميلادي</label>
  <div class="calc"><input type="number" id="hD" min="1" max="30" value="1" style="width:80px" class="num" aria-label="اليوم"><select id="hM" aria-label="الشهر">%(mopts)s</select><input type="number" id="hY" value="%(hy)d" style="width:100px" class="num" aria-label="السنة"></div>
  <div class="res" id="hOut">—</div>
</div>
<h2>تقويم شهر %(mname)s %(hy)d</h2>
<table><tr><th>الهجري</th><th>اليوم</th><th>الميلادي</th></tr>%(rows)s</table>
<h2>المناسبات القادمة</h2>
<div class="chips">%(ev)s</div>
%(faq)s
''' % dict(wd=WDAYS[TODAY.weekday()], h=hstr(H_TODAY), g=gdate(TODAY), iso=TODAY.isoformat(), hy=H_TODAY[0] if H_TODAY else 1448,
           mname=H_MONTHS[H_TODAY[1] - 1] if H_TODAY else '', rows=rows,
           mopts=''.join('<option value="%d"%s>%s</option>' % (i + 1, ' selected' if H_TODAY and i + 1 == H_TODAY[1] else '', m) for i, m in enumerate(H_MONTHS)),
           ev=''.join('<a href="/%s-countdown">%s %s: بعد %d يوماً</a>' % ({'ramadan': 'ramadan', 'fitr': 'eid-al-fitr', 'adha': 'eid-al-adha'}[k], n, y, left) for k, n, y, d, left in next_events),
           faq=faq_html(qas))
JS = r'''<script>
(function(){
var HM=%s, WD=["الأحد","الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت"], GM=%s;
var F=new Intl.DateTimeFormat("en-u-ca-islamic-umalqura",{day:"numeric",month:"numeric",year:"numeric",timeZone:"UTC"});
function toH(d){ var p=F.formatToParts(d), g=function(t){return +p.find(function(x){return x.type===t;}).value;}; return [g("year"),g("month"),g("day")]; }
function hs(h){ return h[2]+" "+HM[h[1]-1]+" "+h[0]+" هـ"; }
function gs(d){ return d.getUTCDate()+" "+GM[d.getUTCMonth()]+" "+d.getUTCFullYear()+" م"; }
var n=new Date(), t=new Date(Date.UTC(n.getFullYear(),n.getMonth(),n.getDate(),12));
document.getElementById("hNow").textContent=hs(toH(t)); document.getElementById("gNow").textContent="الموافق "+gs(t); document.getElementById("hWd").textContent=WD[t.getUTCDay()];
function g2h(){ var v=document.getElementById("gIn").value; if(!v) return; var d=new Date(v+"T12:00:00Z"); document.getElementById("gOut").textContent=WD[d.getUTCDay()]+" "+hs(toH(d)); }
function h2g(){ var y=+document.getElementById("hY").value, m=+document.getElementById("hM").value, dd=+document.getElementById("hD").value, out=document.getElementById("hOut");
  if(!y||!m||!dd){ out.textContent="—"; return; }
  var est=new Date(Date.UTC(622,6,16,12)+((y-1)*354.367+(m-1)*29.53+(dd-1))*86400000);
  for(var k=-40;k<=40;k++){ var c=new Date(est.getTime()+k*86400000), h=toH(c); if(h[0]===y&&h[1]===m&&h[2]===dd){ out.textContent=WD[c.getUTCDay()]+" "+gs(c); return; } }
  out.textContent="تاريخ غير موجود (الشهر 29 أو 30 يوماً)"; }
["gIn"].forEach(function(i){ document.getElementById(i).oninput=g2h; }); ["hD","hM","hY"].forEach(function(i){ document.getElementById(i).oninput=h2g; document.getElementById(i).onchange=h2g; });
g2h(); h2g();
})();
</script>''' % (json.dumps(H_MONTHS, ensure_ascii=False), json.dumps(G_MONTHS, ensure_ascii=False))
write('hijri-date.html', page('/hijri-date', esc('التاريخ الهجري اليوم %s — تحويل التاريخ من ميلادي إلى هجري | OraNW' % hstr(H_TODAY)),
      esc('التاريخ الهجري اليوم %s %s الموافق %s م حسب تقويم أم القرى، مع محوّل التاريخ من الميلادي إلى الهجري وبالعكس وتقويم الشهر الهجري.' % (WDAYS[TODAY.weekday()], hstr(H_TODAY), gdate(TODAY))),
      body, extra_css=CSS, schema=faq_schema(qas)).replace('</body>', JS + '\n</body>'))
NEW_PATHS.append('/hijri-date')

# ======================= 2) حاسبة الزكاة =======================
archive = json.load(open(os.path.join(ROOT, 'archive.json'), encoding='utf-8'))
g_e = next((e for e in reversed(archive) if e.get('gold')), None)
fx_e = next((e for e in reversed(archive) if e.get('fx')), None)
fx = dict((fx_e or {}).get('fx') or {})
PEG = {'SAR': 3.75, 'AED': 3.6725, 'QAR': 3.64, 'BHD': 0.376, 'OMR': 0.3845, 'JOD': 0.709}
for k, v in PEG.items(): fx.setdefault(k, v)
fx['USD'] = 1.0
CURS = [('SAR', 'ريال سعودي'), ('AED', 'درهم إماراتي'), ('KWD', 'دينار كويتي'), ('QAR', 'ريال قطري'), ('BHD', 'دينار بحريني'), ('OMR', 'ريال عماني'),
        ('EGP', 'جنيه مصري'), ('JOD', 'دينار أردني'), ('IQD', 'دينار عراقي'), ('MAD', 'درهم مغربي'), ('DZD', 'دينار جزائري'), ('TRY', 'ليرة تركية'), ('USD', 'دولار أمريكي'), ('EUR', 'يورو')]
CURS = [(c, n) for c, n in CURS if fx.get(c)]
gold = g_e['gold'] if g_e else None
nis_usd = gold / OZ * 85 if gold else None
nrows = ''.join('<tr%s><td>%s</td><td class="num">%s %s</td></tr>' % (' class="hl"' if c == 'SAR' else '', n, fmt(nis_usd * fx[c], 0 if nis_usd * fx[c] > 10000 else 2), c) for c, n in CURS) if nis_usd else ''
nis_sar = fmt(nis_usd * fx['SAR'], 2) if nis_usd else '—'
qas = [
    ('كم نصاب الزكاة اليوم؟', 'نصاب زكاة المال يعادل قيمة 85 غراماً من الذهب الخالص، وهو اليوم نحو %s ريال سعودي حسب سعر الذهب في %s.' % (nis_sar, g_e['d'] if g_e else '')),
    ('كم نسبة زكاة المال؟', 'زكاة المال ربع العشر، أي 2.5٪ من المال الذي بلغ النصاب وحال عليه الحول (سنة هجرية كاملة).'),
    ('هل تجب الزكاة في ذهب الزينة؟', 'اختلف العلماء في ذهب الزينة المستعمل؛ فمنهم من يوجب فيه الزكاة ومنهم من لا يوجبها. الحاسبة تتيح لك إدخاله أو تركه حسب ما تأخذ به.'),
    ('لماذا يختلف النصاب بين المواقع؟', 'لأن بعضها يحسبه بالفضة (595 غراماً) وهو أقل بكثير، وبعضها بالذهب، ولأن سعر الذهب يتغير يومياً.'),
]
body = '''<h1>حاسبة الزكاة</h1>
<p class="lead">احسب زكاة مالك بالنصاب المحدَّث حسب سعر الذهب اليوم (%(d)s).</p>
<div class="card">
  <div class="note">نصاب الزكاة اليوم (قيمة 85 غرام ذهب عيار 24)</div>
  <div class="big num">%(nis)s <span style="font-size:18px">ريال</span></div>
</div>
<h2>احسب زكاتك</h2>
<div class="card">
  <div class="calc"><label style="width:100%%">العملة</label><select id="cur">%(copts)s</select></div>
  <div class="grid2">
    <div><label>النقد والأرصدة البنكية</label><input id="cash" type="number" inputmode="decimal" min="0" placeholder="0" class="num"></div>
    <div><label>الاستثمارات والأسهم وعروض التجارة</label><input id="inv" type="number" inputmode="decimal" min="0" placeholder="0" class="num"></div>
    <div><label>ذهب (بالغرام)</label><input id="gg" type="number" inputmode="decimal" min="0" placeholder="0" class="num"></div>
    <div><label>عيار الذهب</label><select id="gk"><option value="24">24</option><option value="22">22</option><option value="21" selected>21</option><option value="18">18</option></select></div>
    <div><label>قيمة الفضة التي تملكها</label><input id="silver" type="number" inputmode="decimal" min="0" placeholder="0" class="num"></div>
    <div><label>ديون لك ترجو سدادها</label><input id="recv" type="number" inputmode="decimal" min="0" placeholder="0" class="num"></div>
    <div><label>ديون عليك مستحقة الآن</label><input id="debt" type="number" inputmode="decimal" min="0" placeholder="0" class="num"></div>
  </div>
  <div style="margin-top:14px;border-top:1px solid var(--bd);padding-top:12px">
    <div class="note" id="tot">مجموع المال الخاضع للزكاة: —</div>
    <div class="note" id="nis">النصاب: —</div>
    <div class="res num" id="zak">—</div>
  </div>
</div>
<p class="note">الحاسبة للتقدير والاستئناس. للحالات الخاصة (الشركات، الديون المتعثرة، الرواتب المتراكمة) راجع أهل العلم أو جهة الزكاة الرسمية في بلدك.</p>
<h2>نصاب الزكاة اليوم بعملات أخرى</h2>
<table><tr><th>العملة</th><th>النصاب</th></tr>%(nrows)s</table>
<h2>شروط وجوب الزكاة</h2>
<ul><li><strong>بلوغ النصاب:</strong> أن يبلغ مالك قيمة 85 غراماً من الذهب أو أكثر.</li><li><strong>حولان الحول:</strong> أن يمر على امتلاك النصاب سنة هجرية كاملة.</li><li><strong>الملك التام:</strong> أن يكون المال ملكك وتتصرف فيه.</li></ul>
<p>مقدار الزكاة <strong>2.5٪</strong> (ربع العشر) من المال كله وليس مما زاد على النصاب فقط. ويمكنك معرفة <a href="/hijri-date">التاريخ الهجري اليوم</a> لتحديد موعد حولك، ومتابعة <a href="/gold">سعر الذهب</a> يومياً.</p>
%(faq)s
''' % dict(d=g_e['d'] if g_e else '', nis=nis_sar, copts=''.join('<option value="%s"%s>%s (%s)</option>' % (c, ' selected' if c == 'SAR' else '', n, c) for c, n in CURS), nrows=nrows, faq=faq_html(qas))
JS = r'''<script>
(function(){
var GOLD=%s, FX=%s, P={24:1,22:22/24,21:21/24,18:0.75};
try{ var sv=localStorage.getItem("zakat-cur"); if(sv&&FX[sv]) document.getElementById("cur").value=sv; }catch(e){}
function v(i){ return parseFloat(document.getElementById(i).value)||0; }
function f(x,c){ return x.toLocaleString("en-US",{maximumFractionDigits:x>10000?0:2})+" "+c; }
function calc(){
  var c=document.getElementById("cur").value, r=FX[c], g1=GOLD/31.1035*r;
  var goldVal=v("gg")*g1*P[+document.getElementById("gk").value];
  var total=v("cash")+v("inv")+goldVal+v("silver")+v("recv")-v("debt"), nis=85*g1;
  document.getElementById("tot").textContent="مجموع المال الخاضع للزكاة: "+f(Math.max(0,total),c)+(goldVal?" (منها ذهب بقيمة "+f(goldVal,c)+")":"");
  document.getElementById("nis").textContent="النصاب: "+f(nis,c);
  var z=document.getElementById("zak");
  if(total<=0) z.textContent="أدخل أموالك لحساب الزكاة";
  else if(total<nis) z.textContent="لم يبلغ مالك النصاب، فلا زكاة عليه";
  else z.textContent="الزكاة الواجبة: "+f(total*0.025,c);
}
document.querySelectorAll("input,select").forEach(function(e){ e.addEventListener("input",calc); e.addEventListener("change",calc); });
document.getElementById("cur").addEventListener("change",function(){ try{localStorage.setItem("zakat-cur",this.value);}catch(e){} });
calc();
})();
</script>''' % (gold or 0, json.dumps({c: fx[c] for c, _ in CURS}))
write('zakat-calculator.html', page('/zakat-calculator', esc('حاسبة الزكاة %d — نصاب الزكاة اليوم %s ريال حسب سعر الذهب | OraNW' % (TODAY.year, nis_sar)),
      esc('حاسبة الزكاة: احسب زكاة مالك والذهب والأسهم بنسبة 2.5%%. نصاب الزكاة اليوم %s ريال (قيمة 85 غرام ذهب) ويتحدث يومياً حسب سعر الذهب، بعملات الدول العربية.' % nis_sar),
      body, extra_css=CSS, schema=faq_schema(qas)).replace('</body>', JS + '\n</body>'))
NEW_PATHS.append('/zakat-calculator')

# ======================= 3) عدّادات المناسبات =======================
EV_META = {
    'ramadan': ('ramadan-countdown', 'رمضان', 'شهر رمضان', 'أول أيام رمضان',
                'يبدأ شهر رمضان بعد إكمال شعبان أو رؤية الهلال، وهو شهر الصيام. التاريخ هنا حسب تقويم أم القرى، وتعلن كل دولة بدايته رسمياً بعد تحري الهلال ليلة 29 شعبان.'),
    'fitr': ('eid-al-fitr-countdown', 'عيد الفطر', 'عيد الفطر المبارك', 'أول أيام عيد الفطر',
             'عيد الفطر هو أول أيام شهر شوال، بعد انتهاء صيام رمضان. يُستحب إخراج زكاة الفطر قبل صلاة العيد.'),
    'adha': ('eid-al-adha-countdown', 'عيد الأضحى', 'عيد الأضحى المبارك', 'أول أيام عيد الأضحى',
             'عيد الأضحى يوم العاشر من ذي الحجة، بعد يوم عرفة، ويستمر مع أيام التشريق. يُستحب صيام يوم عرفة لغير الحاج.'),
}
for key, (slug, short, full, first, about) in EV_META.items():
    ups = [(y, datetime.date.fromisoformat(d)) for y, d in EVENTS[key] if datetime.date.fromisoformat(d) >= TODAY]
    y, d = ups[0]
    left = (d - TODAY).days
    others = ''.join('<tr><td>%s %s هـ</td><td class="num">%s</td></tr>' % (short, yy, gdate(dd)) for yy, dd in ups)
    links = ''.join('<a href="/%s">كم باقي على %s</a>' % (m[0], m[1]) for k2, m in EV_META.items() if k2 != key) + '<a href="/hijri-date">التاريخ الهجري اليوم</a>'
    qas = [
        ('كم باقي على %s %s؟' % (short, y), 'باقي %d يوماً على %s %s هـ، المتوقع يوم %s %s حسب تقويم أم القرى.' % (left, short, y, WDAYS[d.weekday()], gdate(d))),
        ('متى %s %s؟' % (first, y), '%s متوقع يوم %s %s م، وقد يختلف يوماً واحداً حسب رؤية الهلال في كل دولة.' % (first, WDAYS[d.weekday()], gdate(d))),
    ]
    body = '''<h1>كم باقي على %(short)s %(y)s؟</h1>
<p class="lead">%(first)s متوقع يوم %(wd)s %(g)s م حسب تقويم أم القرى.</p>
<div class="card" style="text-align:center">
  <div class="note">باقي على %(full)s</div>
  <div class="cd" aria-live="polite"><div><b id="cD">%(left)d</b><span>يوم</span></div><div><b id="cH">0</b><span>ساعة</span></div><div><b id="cM">0</b><span>دقيقة</span></div><div><b id="cS">0</b><span>ثانية</span></div></div>
  <div class="note" id="cMsg"></div>
</div>
<p>%(about)s</p>
<h2>مواعيد %(short)s في السنوات القادمة</h2>
<table><tr><th>المناسبة</th><th>التاريخ المتوقع</th></tr>%(others)s</table>
<p class="note">التواريخ فلكية حسب تقويم أم القرى، والإعلان الرسمي يكون من الجهات المختصة في كل دولة.</p>
%(faq)s
<h2>عدّادات أخرى</h2>
<div class="chips">%(links)s</div>
''' % dict(short=short, y=y, first=first, wd=WDAYS[d.weekday()], g=gdate(d), full=full, left=left, about=about, others=others, faq=faq_html(qas), links=links)
    JS = '''<script>
(function(){
var T=new Date(%d,%d,%d,0,0,0);
function p(n){return n<10?"0"+n:n;}
function tick(){ var ms=T-new Date();
  if(ms<=0){ document.getElementById("cMsg").textContent="%s — كل عام وأنتم بخير"; ms=0; }
  var s=Math.floor(ms/1000); document.getElementById("cD").textContent=Math.floor(s/86400); document.getElementById("cH").textContent=p(Math.floor(s%%86400/3600));
  document.getElementById("cM").textContent=p(Math.floor(s%%3600/60)); document.getElementById("cS").textContent=p(s%%60); }
tick(); setInterval(tick,1000);
})();
</script>''' % (d.year, d.month - 1, d.day, 'جاء ' + full)
    title = 'كم باقي على %s %s؟ العد التنازلي — %d يوماً | OraNW' % (short, y, left)
    desc = 'كم باقي على %s %s: %d يوماً. %s متوقع يوم %s %s م حسب تقويم أم القرى، مع عدّاد تنازلي بالأيام والساعات والدقائق.' % (short, y, left, first, WDAYS[d.weekday()], gdate(d))
    write(slug + '.html', page('/' + slug, esc(title), esc(desc), body, extra_css=CSS, schema=faq_schema(qas)).replace('</body>', JS + '\n</body>'))
    NEW_PATHS.append('/' + slug)

# ======================= خريطة الموقع =======================
sp = os.path.join(ROOT, 'sitemap.xml')
s = open(sp, encoding='utf-8').read()
for p_ in NEW_PATHS:
    if '<loc>https://oranw.com%s</loc>' % p_ not in s:
        s = s.replace('</urlset>', '  <url><loc>https://oranw.com%s</loc><lastmod>%s</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>\n</urlset>' % (p_, TODAY.isoformat()))
open(sp, 'w', encoding='utf-8').write(s)
print('extra pages built:', ', '.join(NEW_PATHS), '| hijri today:', hstr(H_TODAY))
