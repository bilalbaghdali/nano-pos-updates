#!/usr/bin/env python3
"""Create one offline, source-attributed set of 80 Quran verses and 20 Sahih hadith.
Quran text and Arabic tafsir from alquran.cloud quran-uthmani + ar.muyassar editions.
Hadith excerpts are checked against the Arabic Sahih record on sunnah.com.
Stops build rather than publishing unsupported religious text.
"""
import html,json,re,sys,urllib.request,unicodedata,time
from pathlib import Path
from html.parser import HTMLParser

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path("faith-items.js")
VERSE_KEYS="""
1:2 1:5
2:45 2:153 2:156 2:186 2:195 2:216 2:263 2:280 2:286
3:8 3:92 3:103 3:134 3:139 3:159 3:173 3:200
4:36 4:58 4:86 4:114
5:2 5:8 5:100
6:141 6:160
7:31 7:199
8:46
9:51 9:119
10:57 10:62
11:114 11:115
12:64 12:87 12:92
13:11 13:28
14:7 14:41
15:49
16:90 16:97
17:23 17:24 17:53
18:10 18:46
20:25 20:26 20:114
21:87 21:107
22:77
23:1 23:2
24:30
25:63 25:74
27:19
28:24
29:69
30:21
31:17 31:18
33:21 33:70
39:53
40:60
41:34
49:10 49:13
59:18
65:3
93:5
94:5
""".split()
# Excerpts only: all of these must be verified in the Arabic of their
# linked hadith record. Hadith explanations are clearly short paraphrases.
HADITH=[
 ("bukhari:1","إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ","الأعمال تتفاوت قيمتها بحسب النية والقصد."),
 ("bukhari:10","الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ","من كمال الإسلام كف أذى اللسان واليد عن الآخرين."),
 ("bukhari:13","لَا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لِأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ","يحُث الحديث على حب الخير للغير مثل حبه للنفس."),
 ("bukhari:39","إِنَّ الدِّينَ يُسْرٌ","في الحديث بيان أن الشريعة مبنية على اليسر وعدم التشدد."),
 ("bukhari:71","مَنْ يُرِدِ اللَّهُ بِهِ خَيْرًا يُفَقِّهْهُ فِي الدِّينِ","تعلم الدين وفهمه من أبواب الخير."),
 ("bukhari:52","أَلَا وَإِنَّ فِي الْجَسَدِ مُضْغَةً","يربط الحديث صلاح العمل بصلاح القلب."),
 ("bukhari:33","آيَةُ الْمُنَافِقِ ثَلَاثٌ","يحذّر الحديث من الكذب وإخلاف الوعد وخيانة الأمانة."),
 ("bukhari:2076","رَحِمَ اللَّهُ رَجُلًا سَمْحًا إِذَا بَاعَ","السماحة واللين من الآداب المحمودة في التجارة."),
 ("bukhari:6018","فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ","التوجيه إلى الكلمة الطيبة والبعد عن الكلام المؤذي."),
 ("bukhari:6114","لَيْسَ الشَّدِيدُ بِالصُّرَعَةِ","القوة المحمودة تشمل السيطرة على النفس وقت الغضب."),
 ("bukhari:6412","نِعْمَتَانِ مَغْبُونٌ فِيهِمَا كَثِيرٌ مِنَ النَّاسِ","ينبّه الحديث إلى قيمة الصحة والفراغ واغتنامهما."),
 ("bukhari:5027","خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ","فضيلة تعلم القرآن ونفع الآخرين بتعليمه."),
 ("bukhari:6464","أَحَبَّ الأَعْمَالِ أَدْوَمُهَا إِلَى اللَّهِ","المداومة على العمل الصالح من أسباب فضله ولو كان قليلاً."),
 ("bukhari:2989","وَالْكَلِمَةُ الطَّيِّبَةُ صَدَقَةٌ","الكلمة الطيبة من صور البر والإحسان إلى الناس."),
 ("muslim:2699a","وَاللَّهُ فِي عَوْنِ الْعَبْدِ مَا كَانَ الْعَبْدُ فِي عَوْنِ أَخِيهِ","مساعدة الآخرين من أسباب معونة الله للعبد."),
 ("muslim:2588","مَا نَقَصَتْ صَدَقَةٌ مِنْ مَالٍ","للصدقة بركة وثواب، ولا يخسر المتصدق أجرها."),
 ("muslim:91","إِنَّ اللَّهَ جَمِيلٌ يُحِبُّ الْجَمَالَ","الجمال المشروع لا ينافي التواضع، والتكبر هو المذموم."),
 ("muslim:55a","الدِّينُ النَّصِيحَةُ","النصيحة الصادقة من حقوق الدين والتعامل الحسن."),
 ("muslim:1893a","مَنْ دَلَّ عَلَى خَيْرٍ فَلَهُ مِثْلُ أَجْرِ فَاعِلِهِ","إرشاد الغير إلى العمل الصالح له أجر عظيم."),
 ("muslim:2690a","اللَّهُمَّ آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ","دعاء جامع لخير الدنيا والآخرة وطلب الوقاية من النار.")
]

def fetch(url,timeout=50):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; NANO-POS-SourceCheck/1.0)","Accept":"application/json,text/html"})
    last=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:
                if r.status!=200:raise ValueError(f"HTTP {r.status}")
                return r.read()
        except Exception as ex:
            last=ex
            if attempt<2:time.sleep(1+attempt)
    raise RuntimeError(f"Unable to retrieve verified source {url}: {last}")

def norm(s):
    s=unicodedata.normalize("NFKD",html.unescape(s))
    s="".join(c for c in s if not unicodedata.combining(c) and c not in "ـ\u200f\u200e")
    s=re.sub("[إأآٱ]","ا",s).replace("ى","ي").replace("ة","ه")
    return re.sub(r"[^\u0621-\u064a]+","",s)

class ArabicParser(HTMLParser):
    def __init__(self):super().__init__();self.fragments=[];self.depth=0
    def handle_starttag(self,tag,attrs):
        classes=dict(attrs).get("class","")
        if "arabic_hadith_full" in classes:self.depth=1
        elif self.depth:self.depth+=1
    def handle_endtag(self,tag):
        if self.depth:self.depth-=1
    def handle_data(self,data):
        if self.depth:self.fragments.append(data)

def quran():
    base="https://api.alquran.cloud/v1/quran/"
    full=json.loads(fetch(base+"quran-uthmani").decode("utf8"))
    tafsir=json.loads(fetch(base+"ar.muyassar").decode("utf8"))
    if full.get("code")!=200 or tafsir.get("code")!=200:raise ValueError("Quran API returned non-OK")
    q={f"{surah['number']}:{a['numberInSurah']}":(a["text"],surah["name"])
       for surah in full["data"]["surahs"] for a in surah["ayahs"]}
    t={f"{surah['number']}:{a['numberInSurah']}":a["text"] for surah in tafsir["data"]["surahs"] for a in surah["ayahs"]}
    assert len(q)>=6200 and len(t)>=6200 and len(VERSE_KEYS)==80, (len(q),len(t),len(VERSE_KEYS))
    out=[]
    for key in VERSE_KEYS:
        verse,name=q[key];explanation=t[key]
        if len(verse)<5 or len(explanation)<8:raise ValueError("Empty Quran text or tafsir "+key)
        # Full verse exact; long tafsir may be truncated with clear "excerpt" attribution.
        excerpt=explanation.strip()
        if len(excerpt)>430:
            stop=excerpt.rfind(" ",0,430)
            excerpt=excerpt[:stop if stop>260 else 430]+"…"
        out.append(dict(id="q-"+key,type="آية كريمة",text=verse,
            reference=f"{name} — الآية {key.split(':')[1]} ({key})",
            explanation=excerpt,
            source="مقتطف من التفسير الميسر — مجمع الملك فهد لطباعة المصحف الشريف",
            url="https://quran.com/ar/"+key,origin="https://api.alquran.cloud/v1/ayah/"+key+"/ar.muyassar"))
    return out

def hadith():
    out=[];errors=[]
    for code,excerpt,summary in HADITH:
        url="https://sunnah.com/"+code
        page=fetch(url,timeout=25).decode("utf8")
        parser=ArabicParser();parser.feed(page)
        arabic=" ".join(parser.fragments)
        if not arabic:
            errors.append(f"Missing authenticated Arabic Sahih text {code}");continue
        if norm(excerpt) not in norm(arabic):
            errors.append(f"Hadith quote not verified: {code}, {excerpt!r} (arabic length={len(arabic)})");continue
        reference=("صحيح البخاري " if code.startswith("bukhari") else "صحيح مسلم ")+code.split(":")[1]
        out.append(dict(id="h-"+code,type="حديث صحيح",text=excerpt,reference=reference,
                        explanation=summary,source=reference+" — معنى موجز مستفاد من الحديث",
                        url=url))
    if errors:raise ValueError("\\n".join(errors))
    return out

def main():
    verses=quran()
    ahadith=hadith()
    assert len(verses)==80 and len(ahadith)==20
    # Interleave one hadith per four Quran verses.
    items=[]
    for i in range(20):
        items.extend(verses[i*4:(i+1)*4])
        items.append(ahadith[i])
    ids=[x["id"] for x in items]
    texts=[norm(x["text"]) for x in items]
    if len(items)!=100 or len(set(ids))!=100 or len(set(texts))!=100:raise ValueError("Not 100 unique source texts")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text("(function(){\n'use strict';\nwindow.NANO_FAITH_ITEMS_183="+json.dumps(items,ensure_ascii=False,separators=(',',':'))+";\n})();\n",encoding="utf8")
    print("VERIFIED 100 DISTINCT REMINDERS:",len(verses),"Quran verses +",len(ahadith),"Sahih hadith")
    print("OUTPUT",OUT,OUT.stat().st_size,"bytes")
    print("QURAN_SAMPLES",[(v["id"],v["reference"],v["text"][:30]) for v in verses[:3]])
    print("HADITH_SAMPLES",[(v["id"],v["text"][:60]) for v in ahadith[:3]])

if __name__=="__main__":main()
