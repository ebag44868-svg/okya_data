# okya-data — 창녕옥야고 급식·학사일정 자동 배포

옥야앱(`index.html`)이 읽어가는 급식/학사일정 JSON을 **매일 밤 12시(KST) 자동 갱신**해서
GitHub Pages로 공개하는 저장소입니다. NEIS 오픈API에서 데이터를 받아옵니다.

- `meal.json` — 오늘~약 6주치 급식(조·중·석). GitHub Actions가 매일 자정 갱신.
- `schedule.json` — 이번 학년도 학사일정. (연 1회성 데이터)
- `scripts/fetch_neis.py` — NEIS 수집 스크립트
- `.github/workflows/update-meal.yml` — 매일 자정 자동 실행

학교 코드: 경상남도교육청 `S10` / 창녕옥야고 `9010330` (스크립트에 하드코딩)

---

## 내가 할 일 (딱 4단계)

### 1. 이 폴더를 GitHub 저장소로 올리기
`okya-data` 폴더를 새 GitHub 저장소(예: `okya-data`)에 **public**으로 push.
```bash
cd okya-data
git init
git add .
git commit -m "init: 옥야 급식·학사일정 데이터"
git branch -M main
git remote add origin https://github.com/<내아이디>/okya-data.git
git push -u origin main
```

### 2. GitHub Pages 켜기
저장소 → **Settings → Pages** →
Source: **Deploy from a branch**, Branch: **main / (root)** → Save.
1~2분 뒤 `https://<내아이디>.github.io/okya-data/meal.json` 로 접속되면 성공.

### 3. 앱에 주소 연결
`okss/index.html` 상단의 이 줄을 **내 Pages 주소로** 수정:
```js
const DATA_BASE='https://YOUR_GH_ID.github.io/okya-data'
// 예: const DATA_BASE='https://shinechan0904.github.io/okya-data'
```
→ 앱을 열면 급식이 실데이터로 뜸. (Pages는 CORS 허용이라 웹/앱 모두 OK)

### 4. (권장) NEIS 무료 인증키 등록 — 조회 제한 해제
키가 없어도 급식은 잘 나오지만, **학사일정은 키가 없으면 몇 건만** 옵니다.
1. https://open.neis.go.kr → 회원가입 → **인증키 신청**(즉시 발급, 무료)
2. 저장소 → **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `NEIS_KEY`
   - Secret: 발급받은 키
3. 끝. 다음 자동 실행부터 전체 일정이 들어옵니다.

---

## 자동 갱신 확인 / 수동 실행
- 저장소 **Actions** 탭 → "급식·학사일정 자동 갱신" → **Run workflow** 로 즉시 테스트 가능.
- 매일 15:00 UTC(= 한국시간 00:00)에 자동 실행됩니다.
- 데이터가 바뀌면 자동 커밋 → Pages가 갱신됨. (변경 없으면 커밋 생략)

## 학사일정이 비어있다면?
NEIS에 학교가 등록한 일정이 적을 수 있습니다. 학사일정은 매년 고정이므로
`schedule.json`의 `events` 배열을 **직접 손으로 채워도** 됩니다:
```json
{ "events": [ {"date":"2026-07-25","label":"기말고사 시작"}, ... ] }
```
(직접 채운 경우, 자동 스크립트가 덮어쓰지 않도록 워크플로에서 schedule 부분을 빼거나
`fetch_neis.py`의 schedule 저장 로직을 주석 처리하세요.)
