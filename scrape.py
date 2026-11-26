"""Preview a dated YIML schedule from saved public HTML. No network by default."""
import argparse
import datetime as dt
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo
from html.parser import HTMLParser

class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
        self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.skip+=1
        if tag in ('div','p','li','tr','br','h1','h2','h3','h4'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
        if tag in ('div','p','li','tr','h1','h2','h3','h4'): self.parts.append('\n')
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)

def parse(html, expected):
    p=Text()
    p.feed(html)
    text=' '.join(''.join(p.parts).split()).replace('’', "'")
    dates=re.findall(r'\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+([A-Z][a-z]+ \d{1,2}, \d{4})',text)
    if not dates or {dt.datetime.strptime(d,'%B %d, %Y').date() for d in dates}!={expected}:
        raise ValueError('Missing, conflicting or stale page date')
    sections=re.findall(r"Today's Calendar\s*(.*?)Today's Zmanim",text,re.I)
    if len(sections)!=1: raise ValueError('Calendar section not uniquely identified')
    pattern=r'\b((?:Early |Late )?(?:Shacharis|Shacharit|Mincha\s*/\s*Maariv|Mincha|Maariv))\s*:\s*(\d{1,2}:\d{2}\s*[AP]M)\b'
    rows=[]
    for label,time in re.findall(pattern,sections[0],re.I):
        typ=re.sub(r'^(Early|Late) ','',label,flags=re.I).replace(' ','').lower()
        typ={'shacharis':'Shacharis','shacharit':'Shacharis','mincha':'Mincha','maariv':'Maariv','mincha/maariv':'Mincha/Maariv'}[typ]
        clock=dt.datetime.strptime(time.upper(),'%I:%M %p').strftime('%H:%M')
        if any(r['type']==typ and r['time']==clock for r in rows): continue
        rows.append(dict(id=f'yiml-{expected}-{len(rows)}',name='Young Israel of the Main Line',area='Bala Cynwyd',type=typ,time=clock,days='daily',date=str(expected),url='https://www.yiml.org/',published=True,verification='dated_published',lastVerified=None))
    if not rows: raise ValueError('No recognized services')
    return rows

def main():
    a=argparse.ArgumentParser()
    a.add_argument('html',type=Path)
    a.add_argument('--date',type=dt.date.fromisoformat,default=dt.datetime.now(ZoneInfo('America/New_York')).date())
    args=a.parse_args()
    print(json.dumps(parse(args.html.read_text(encoding='utf-8'),args.date),indent=2))

if __name__=='__main__': main()
