# 워드프레스 주식 블로그 자동화 (WordPress Stock Blog Automation)

이 프로젝트는 매일 자동으로 미국 및 한국 주식 시장 데이터를 수집하고, AI(Gemini)를 사용하여 고품질의 블로그 포스팅을 생성한 후 워드프레스에 게시하는 파이썬 자동화 도구입니다.

## 🚀 주요 기능 업데이트 (v2.0)

### 1. 🇺🇸 미국 / 🇰🇷 한국 시장 이원화 모드
*   **자동 감지**: 실행 시간에 따라 자동으로 모드를 결정합니다.
    *   **오전 (00:00 ~ 12:00)**: 미국 증시 리포트 (전날 마감 기준)
    *   **오후 (12:00 ~ 24:00)**: 한국 증시 리포트 (당일 마감 기준)
*   **수동 실행**: 커맨드 라인 인자로 모드를 강제할 수 있습니다. (`--mode US`, `--mode KR`)

### 2. 🎨 Elementor UX 최적화 레이아웃
*   **모바일 퍼스트**: 모바일 환경에서 가독성이 극대화되도록 설계되었습니다.
*   **핵심 요약 박스**: 바쁜 사용자를 위해 최상단에 "오늘의 핵심 3줄" 요약 박스를 배치했습니다.
*   **시장 지수 카드**: 다우, 나스닥, 코스피 등 주요 지수를 직관적인 카드 형태로 시각화했습니다. (상승/하락 색상 구분)

### 3. 🔍 강력한 SEO (검색 엔진 최적화)
*   **Yoast SEO 연동**: AI가 선정한 '핵심 키워드(Focus Keyphrase)'를 Yoast 플러그인 설정에 자동 입력합니다.
*   **메타 데이터 최적화**: 제목, 슬러그, 메타 설명, 본문 첫 문장 등에 키워드를 배치하여 SEO 점수를 극대화합니다.
*   **내부/외부 링크**: 신뢰할 수 있는 외부 사이트 및 내 블로그 메인 링크를 자동으로 삽입합니다.

### 4. 🖼️ AI 자동 이미지 생성
*   **Pollinations.ai 연동**: 글의 주제에 맞는 고화질 이미지를 AI가 실시간으로 생성합니다.
*   **자동 업로드 & 설정**: 생성된 이미지를 워드프레스 미디어 라이브러리에 업로드하고, **대표 이미지(Featured Image)**로 자동 설정합니다.
*   **Alt 태그 자동화**: 이미지의 Alt 속성에 핵심 키워드를 넣어 이미지 SEO까지 챙깁니다.

---

## 🛠️ 설치 및 설정

### 1. 필수 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (.env)
프로젝트 루트에 `.env` 파일을 생성하고 다음 정보를 입력하세요.
```env
WP_URL=https://your-wordpress-site.com
WP_USERNAME=your_username
WP_APP_PASSWORD=your_application_password
GEMINI_API_KEY=your_gemini_api_key
```

### 3. 워드프레스 테마 설정 (필수)
Elementor 및 Yoast SEO 데이터를 외부에서 수정할 수 있도록 테마의 `functions.php`에 메타 키 등록 코드가 필요합니다. (현재 스크립트가 `twentytwentyfour`, `twentytwentyfive` 테마에 대해 자동 적용됨)

---

## 💻 실행 방법

### 기본 실행 (시간 기반 자동 모드)
```bash
python run_automation.py
```

### 모드 지정 실행
```bash
# 미국 주식 리포트 강제 발행
python run_automation.py --mode US

# 한국 주식 리포트 강제 발행
python run_automation.py --mode KR
```

## 📂 파일 구조
*   `run_automation.py`: 핵심 자동화 스크립트
*   `requirements.txt`: 의존성 라이브러리 목록
*   `.env`: 환경 설정 파일 (비공개)
*   `README.md`: 프로젝트 설명서

## 📝 라이선스
이 프로젝트는 개인 학습 및 자동화 목적으로 작성되었습니다.
