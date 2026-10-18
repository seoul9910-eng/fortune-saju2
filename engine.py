"""Korean saju calculation engine. Modern KST (UTC+09), 1962-2049.
Solar terms: Swiss Ephemeris apparent tropical Sun; year at Li Chun 315°, months at 12 jie.
Day boundary: midnight KST. Hour branch: Zi 23:00-00:59.
"""
from datetime import date, datetime, timedelta, timezone
import math
import swisseph as swe
from korean_lunar_calendar import KoreanLunarCalendar

KST=timezone(timedelta(hours=9))
STEMS='甲乙丙丁戊己庚辛壬癸'
BRANCHES='子丑寅卯辰巳午未申酉戌亥'
ELEM=dict(zip(STEMS,['목','목','화','화','토','토','금','금','수','수']))
ELEM.update(dict(zip(BRANCHES,['수','토','목','목','토','화','화','토','금','금','토','수'])))
YANG={s:i%2==0 for i,s in enumerate(STEMS)}
GEN={'목':'화','화':'토','토':'금','금':'수','수':'목'}
CTRL={'목':'토','토':'수','수':'화','화':'금','금':'목'}
HIDDEN={'子':'癸','丑':'己癸辛','寅':'甲丙戊','卯':'乙','辰':'戊乙癸','巳':'丙戊庚','午':'丁己','未':'己丁乙','申':'庚壬戊','酉':'辛','戌':'戊辛丁','亥':'壬甲'}

def jd_utc(dt):
    u=dt.astimezone(timezone.utc)
    return swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600+u.microsecond/3.6e9)

def solar_longitude(dt):
    return swe.calc_ut(jd_utc(dt),swe.SUN,swe.FLG_MOSEPH|swe.FLG_SPEED)[0][0]%360

def crossing_near(dt, target, direction):
    """Next or previous solar longitude crossing (at most 31 days away)."""
    start=solar_longitude(dt)
    delta=(target-start)%360 if direction>0 else (start-target)%360
    if delta<1e-9: return dt
    rough=dt+timedelta(days=direction*delta/0.9856)
    lo=rough-timedelta(days=3)
    hi=rough+timedelta(days=3)
    # Signed modular difference near target, avoiding 0/360 wrap.
    def f(t): return ((solar_longitude(t)-target+180)%360)-180
    if not (f(lo)<0<f(hi)):
        raise ValueError('절기 경계 계산에 실패했습니다.')
    for _ in range(42):
        mid=lo+(hi-lo)/2
        if f(mid)<0: lo=mid
        else: hi=mid
    return lo+(hi-lo)/2

def get_near_jie(dt):
    lon=solar_longitude(dt)
    idx=int(math.floor(((lon-315)%360)/30))
    prev_target=(315+idx*30)%360
    next_target=(prev_target+30)%360
    return crossing_near(dt,prev_target,-1),crossing_near(dt,next_target,1),idx

def solar_from_input(birth,calendar,leap):
    raw=str(birth).strip().replace('-','')
    if len(raw)!=8 or not raw.isdigit():raise ValueError('생년월일은 19920326처럼 숫자 8자리로 입력하세요.')
    y,m,d=int(raw[:4]),int(raw[4:6]),int(raw[6:8])
    if not (1962<=y<=2049):raise ValueError('정확한 한국 표준시 적용을 위해 현재는 1962~2049년 출생만 지원합니다.')
    c=KoreanLunarCalendar()
    if calendar=='solar':
        try: birthdate=date(y,m,d)
        except ValueError:raise ValueError('존재하지 않는 양력 날짜입니다.')
        if not c.setSolarDate(y,m,d):raise ValueError('지원하지 않는 양력 날짜입니다.')
    elif calendar=='lunar':
        if not c.setLunarDate(y,m,d,bool(leap)):raise ValueError('존재하지 않는 음력 날짜입니다.')
        if bool(c.isIntercalation)!=bool(leap):raise ValueError('해당 월은 윤달이 아니거나 윤달 지정이 잘못되었습니다.')
        birthdate=date.fromisoformat(c.SolarIsoFormat())
    else:raise ValueError('양력 또는 음력을 선택해 주세요.')
    return birthdate

def pillar(stem_idx,branch_idx):return STEMS[stem_idx%10]+BRANCHES[branch_idx%12]

def ten_god(day,other):
    a,b=ELEM[day],ELEM[other];same=YANG[day]==YANG[other]
    if a==b:return '비견' if same else '겁재'
    if GEN[a]==b:return '식신' if same else '상관'
    if CTRL[a]==b:return '편재' if same else '정재'
    if CTRL[b]==a:return '편관' if same else '정관'
    if GEN[b]==a:return '편인' if same else '정인'
    raise ValueError('십성 산출 실패')

def day_pillar(solar_date):
    cal=KoreanLunarCalendar()
    if not cal.setSolarDate(solar_date.year,solar_date.month,solar_date.day):
        raise ValueError('일주 계산 지원 범위를 벗어났습니다.')
    return cal.getChineseGapJaString().split()[2][:2]

def get_chart(data):
    solar=solar_from_input(data.get('birth',''),data.get('calendar','solar'),data.get('leap',False))
    hour=data.get('hour','unknown'); minute=int(data.get('minute',0))
    if minute not in range(0,60,10):raise ValueError('출생 분은 10분 단위로 입력해 주세요.')
    if hour=='unknown': h=12; known=False
    else:
        try:h=int(hour)
        except (ValueError,TypeError):raise ValueError('출생 시간을 확인해 주세요.')
        if not 0<=h<=23:raise ValueError('출생 시간은 0~23시입니다.')
        known=True
    dt=datetime(solar.year,solar.month,solar.day,h,minute,tzinfo=KST)
    prev_jie,next_jie,month_idx=get_near_jie(dt)
    # 315° Li Chun is the year boundary. 12 jie determine month pillar.
    lichun=crossing_near(datetime(solar.year,2,4,12,tzinfo=KST),315, -1 if solar_longitude(datetime(solar.year,2,4,12,tzinfo=KST))>=315 else 1)
    # Avoid branch choice near 0° wrap by using month index: 11 => Chou, 0 => Yin.
    solar_year=solar.year if dt>=lichun else solar.year-1
    ys=(solar_year-4)%10;yb=(solar_year-4)%12
    year=pillar(ys,yb)
    month=pillar((ys%5*2+2+month_idx)%10,(2+month_idx)%12)
    day=day_pillar(solar)
    hour_p=None
    if known:
        hb=((h+1)//2)%12
        hour_p=pillar((STEMS.index(day[0])%5*2+hb)%10,hb)
    pillars={'year':year,'month':month,'day':day,'hour':hour_p}
    counts={k:0 for k in ['목','화','토','금','수']}
    for p in pillars.values():
        if p:
            counts[ELEM[p[0]]]+=1;counts[ELEM[p[1]]]+=1
    daystem=day[0]
    pitems=[]
    for key,label in [('hour','시주'),('day','일주'),('month','월주'),('year','년주')]:
        p=pillars[key]
        pitems.append({'label':label,'stem':p[0] if p else '—','branch':p[1] if p else '—','stemElement':ELEM[p[0]] if p else None,'branchElement':ELEM[p[1]] if p else None,'ten':ten_god(daystem,p[0]) if p and key!='day' else ('나의 일간' if p else '미확정'),'branchTen':ten_god(daystem,HIDDEN[p[1]][0]) if p else None})
    # Conventional Tian Yi Gui Ren based on day stem (different schools may use year stem too).
    nobles={'甲':'丑未','戊':'丑未','庚':'丑未','乙':'子申','己':'子申','丙':'亥酉','丁':'亥酉','壬':'卯巳','癸':'卯巳','辛':'寅午'}
    matches=[key for key,p in pillars.items() if p and p[1] in nobles[daystem]]
    noble={'present':bool(matches),'positions':matches,'rule':'일간 기준 천을귀인(일부 학파는 연간도 함께 사용)'}
    gender=data.get('gender','')
    luck=[];luck_note='성별을 선택하면 전통 순역행 방식에 따른 대운을 계산합니다.'
    if gender in ('남성','여성'):
        forward=(gender=='남성')==YANG[year[0]]
        boundary=next_jie if forward else prev_jie
        years=abs((boundary-dt).total_seconds())/86400/3
        # 3 days = 1 year; first cycle starts at decimal years after birth.
        start=years
        base_stem=STEMS.index(month[0]);base_branch=BRANCHES.index(month[1])
        for i in range(8):
            sign=1 if forward else -1
            luck_p=pillar(base_stem+sign*(i+1),base_branch+sign*(i+1))
            luck.append({'startAge':round(start+10*i,1),'endAge':round(start+10*(i+1),1),'pillar':luck_p,'ten':ten_god(daystem,luck_p[0])})
        luck_note=('순행' if forward else '역행')+' 대운 · 3일=1년 환산 · 절입 시각 기준. 대운 시작 연령은 학파별 반올림법에 따라 다를 수 있습니다.'
    return {'solar':solar.isoformat(),'birthTime':dt.isoformat() if known else None,'year':year,'month':month,'day':day,'hour':hour_p,'pillars':pitems,'counts':counts,'noble':noble,'luck':luck,'luckNote':luck_note,'solarYear':solar_year,'prevJie':prev_jie.isoformat(),'nextJie':next_jie.isoformat(),'lichun':lichun.isoformat(),'rule':'절기 12절 기준 월주, 입춘 기준 연주, 한국표준시 UTC+9, 자정 기준 일주, 23~01시 자시'}
