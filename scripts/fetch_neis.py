#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
창녕옥야고 급식/학사일정을 NEIS 오픈API에서 받아
meal.json / schedule.json 으로 저장한다.
- API 키 없이도 동작하지만, 넉넉한 조회를 위해 무료 KEY 사용 권장(환경변수 NEIS_KEY).
- GitHub Actions가 매일 자정(KST)에 실행 → 결과를 커밋 → GitHub Pages가 서빙.
"""
import json, os, re, ssl, sys, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone

ATPT = "S10"        # 경상남도교육청
SCHUL = "9010330"   # 창녕옥야고등학교
KEY = os.environ.get("NEIS_KEY", "").strip()
BASE = "https://open.neis.go.kr/hub"
KST = timezone(timedelta(hours=9))
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE  # NEIS 인증서 이슈 회피용(데이터 무결성엔 영향 없음)


def api(endpoint, extra):
    """endpoint를 pIndex로 넘겨가며 전부 받아 row 리스트로 반환."""
    rows, pindex = [], 1
    while True:
        params = {"Type": "json", "pIndex": pindex, "pSize": 1000,
                  "ATPT_OFCDC_SC_CODE": ATPT, "SD_SCHUL_CODE": SCHUL, **extra}
        if KEY:
            params["KEY"] = KEY
        url = f"{BASE}/{endpoint}?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=30, context=CTX) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"[warn] {endpoint} 요청 실패: {e}", file=sys.stderr)
            break
        if endpoint not in data:            # 데이터 없음/에러 → 종료
            break
        block = data[endpoint]
        page = next((b["row"] for b in block if "row" in b), [])
        rows.extend(page)
        if len(page) < 1000:                # 마지막 페이지
            break
        pindex += 1
    return rows


def clean_dishes(ddish):
    """'쌀밥<br/>돈까스 (1.5.6)' → ['쌀밥','돈까스'] (알레르기 표기 제거)."""
    out = []
    for part in re.split(r"<br\s*/?>", ddish or ""):
        name = re.sub(r"\s*\(?[\d\.\s,]+\)?\s*$", "", part)  # 끝의 알레르기 숫자 제거
        name = name.replace("*", "").strip()
        if name:
            out.append(name)
    return out


def fetch_meals():
    """오늘-2일 ~ 오늘+45일 급식을 { 'YYYY-MM-DD': {조식,중식,석식} } 로."""
    today = datetime.now(KST).date()
    frm = (today - timedelta(days=2)).strftime("%Y%m%d")
    to = (today + timedelta(days=45)).strftime("%Y%m%d")
    meals = {}
    for row in api("mealServiceDietInfo", {"MLSV_FROM_YMD": frm, "MLSV_TO_YMD": to}):
        ymd = row.get("MLSV_YMD", "")
        if len(ymd) != 8:
            continue
        key = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
        slot = row.get("MMEAL_SC_NM", "").strip()  # 조식/중식/석식
        if slot not in ("조식", "중식", "석식"):
            continue
        meals.setdefault(key, {}).setdefault(slot, [])
        meals[key][slot] = clean_dishes(row.get("DDISH_NM", ""))
    return meals


def fetch_schedule():
    """이번 학년도(3월~다음해 2월) 학사일정을 [{date,label}] 로."""
    y = datetime.now(KST).year
    frm, to = f"{y}0101", f"{y + 1}0228"
    seen, events = set(), []
    for row in api("SchoolSchedule", {"AA_FROM_YMD": frm, "AA_TO_YMD": to}):
        ymd = row.get("AA_YMD", "")
        label = (row.get("EVENT_NM") or "").strip()
        if len(ymd) != 8 or not label or label in ("토요휴업일",):
            continue
        d = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
        k = (d, label)
        if k in seen:
            continue
        seen.add(k)
        events.append({"date": d, "label": label})
    events.sort(key=lambda e: e["date"])
    return events


def write(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print(f"[ok] {path}: {len(obj.get('meals', obj.get('events', [])))} entries")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    now = datetime.now(KST).isoformat()
    meals = fetch_meals()
    events = fetch_schedule()
    # 데이터를 하나도 못 받으면 기존 파일을 덮어쓰지 않음(사고 방지)
    if meals:
        write(os.path.join(root, "meal.json"), {"updated": now, "school": "창녕옥야고등학교", "meals": meals})
    else:
        print("[warn] 급식 0건 → meal.json 유지", file=sys.stderr)
    if events:
        write(os.path.join(root, "schedule.json"), {"updated": now, "school": "창녕옥야고등학교", "events": events})
    else:
        print("[warn] 학사일정 0건 → schedule.json 유지", file=sys.stderr)


if __name__ == "__main__":
    main()
