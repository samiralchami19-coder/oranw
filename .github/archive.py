#!/usr/bin/env python3
# OraNW — اللقطة اليومية لأرشيف الكوكب
# يعمل تلقائيًا كل ليلة عبر GitHub Actions ويكتب archive.json
import json, math, datetime, os, urllib.request

BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

def get(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': BROWSER_UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode('utf-8', 'ignore')

def stooq(sym):
    # محاولتان مع فاصل — stooq يحظر أحيانًا الطلبات المتتالية
    import time
    for attempt in range(2):
        try:
            csv = get('https://stooq.com/q/l/?s=%s&f=sd2t2ohlcv&h&e=csv' % sym)
            lines = csv.strip().splitlines()
            if len(lines) < 2:
                return None
            return float(lines[1].split(',')[6])  # إغلاق
        except Exception:
            time.sleep(3)
    return None

def coingecko(ids):
    try:
        j = json.loads(get('https://api.coingecko.com/api/v3/simple/price?ids=%s&vs_currencies=usd' % ids))
        return j
    except Exception:
        return None

def btc_price():
    j = coingecko('bitcoin')
    try:
        return float(j['bitcoin']['usd'])
    except Exception:
        return None

def oil_price():
    # النفط: stooq ثم Yahoo Finance
    v = stooq('cl.f')
    if v:
        return v
    try:
        j = json.loads(get('https://query1.finance.yahoo.com/v8/finance/chart/CL%3DF?interval=1d&range=1d'))
        return float(j['chart']['result'][0]['meta']['regularMarketPrice'])
    except Exception:
        return None

def gold_price():
    # الذهب من stooq، والاحتياط: PAX Gold (رمز مرتبط بأونصة الذهب)
    v = stooq('xauusd')
    if v:
        return v
    j = coingecko('pax-gold')
    try:
        return float(j['pax-gold']['usd'])
    except Exception:
        return None

EXT = [
    ("وادي الموت","Death Valley",36.46,-116.87), ("الأزيزية","Al Aziziyah",32.79,12.06),
    ("الرياض","Riyadh",24.71,46.68), ("دلهي","Delhi",28.61,77.21),
    ("بغداد","Baghdad",33.32,44.36), ("الدمام","Dammam",26.43,50.10),
    ("فينيكس","Phoenix",33.45,-112.07), ("كراتشي","Karachi",24.86,67.01),
    ("أويمياكون","Oymyakon",63.46,142.79), ("فوستوك","Vostok",-78.46,106.84),
    ("يلونايف","Yellowknife",62.45,-114.37), ("موسكو","Moscow",55.76,37.62),
    ("أولان باتور","Ulaanbaatar",47.89,106.91), ("هلسنكي","Helsinki",60.17,24.94)
]

def extremes():
    try:
        lats = ','.join(str(e[2]) for e in EXT)
        lngs = ','.join(str(e[3]) for e in EXT)
        j = json.loads(get('https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&current_weather=true' % (lats, lngs)))
        arr = j if isinstance(j, list) else [j]
        bh, bc, hi, ci = -999, 999, 0, 0
        for i, item in enumerate(arr):
            t = item['current_weather']['temperature']
            if t > bh: bh, hi = t, i
            if t < bc: bc, ci = t, i
        return {"n": EXT[hi][0], "ne": EXT[hi][1], "t": round(bh)}, {"n": EXT[ci][0], "ne": EXT[ci][1], "t": round(bc)}
    except Exception:
        return None, None

SYNODIC = 29.53058867
REF_NEW = datetime.datetime(2000, 1, 6, 18, 14, tzinfo=datetime.timezone.utc)

def moon():
    now = datetime.datetime.now(datetime.timezone.utc)
    age = ((now - REF_NEW).total_seconds() / 86400) % SYNODIC
    idx = int(age / (SYNODIC / 8)) % 8
    illum = round((1 - math.cos(2 * math.pi * age / SYNODIC)) / 2 * 100)
    return idx, illum

def day_length(lat, lng):
    # معادلة الشروق/الغروب — نفس حساب الموقع
    rad = math.pi / 180
    N = datetime.datetime.now(datetime.timezone.utc).timetuple().tm_yday
    def calc(is_set):
        lngH = lng / 15
        t = N + ((18 if is_set else 6) - lngH) / 24
        M = 0.9856 * t - 3.289
        L = (M + 1.916 * math.sin(M * rad) + 0.020 * math.sin(2 * M * rad) + 282.634) % 360
        RA = math.atan(0.91764 * math.tan(L * rad)) / rad % 360
        RA += (int(L // 90) * 90 - int(RA // 90) * 90); RA /= 15
        sinDec = 0.39782 * math.sin(L * rad)
        cosH = (math.cos(90.833 * rad) - sinDec * math.sin(lat * rad)) / (math.cos(math.asin(sinDec)) * math.cos(lat * rad))
        if cosH > 1 or cosH < -1: return None
        H = (math.acos(cosH) if is_set else 2 * math.pi - math.acos(cosH)) / rad / 15
        return (H + RA - 0.06571 * t - 6.622 - lngH) % 24
    sr, ss = calc(False), calc(True)
    return round((ss - sr) % 24, 2) if sr is not None and ss is not None else None

hot, cold = extremes()
midx, illum = moon()
entry = {
    "d": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d'),
    "gold": gold_price(),
    "btc": btc_price(),
    "oil": oil_price(),
    "hot": hot, "cold": cold,
    "moon": midx, "illum": illum,
    "dayLen": day_length(24.71, 46.68)  # مرجع: الرياض
}

data = []
if os.path.exists('archive.json'):
    try:
        data = json.load(open('archive.json', encoding='utf-8'))
    except Exception:
        data = []
data = [e for e in data if e.get('d') != entry['d']]  # لا تكرار لنفس اليوم
data.append(entry)
data = data[-400:]
with open('archive.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print('archived:', entry['d'], '| gold:', entry['gold'], '| btc:', entry['btc'], '| oil:', entry['oil'])
