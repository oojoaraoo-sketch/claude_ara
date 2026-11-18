# 탐색·개선 기록 (주간 예약 작업 "콘텐츠 고도화 탐색"이 갱신)

> 매주 탐색한 것(인기 Claude 스킬, 모션 인포그래픽 기법, Claude로 만드는 새 표현, 채널 성장 방법)을 기록하고,
> 쓸 만한 것은 아래 대기열에 넣어 한 주에 하나씩 구현한다. 외부 코드는 그대로 설치·실행하지 않고, 읽고 이해한 뒤 직접 구현한다.

## 대기열 (위에서부터 구현 — 번호는 식별용, 순서는 표의 위아래)
| # | 아이디어 | 기대 효과 | 상태 |
|---|---|---|---|
| 1 | ~~3D 타임랩스 월 1회 자동 게시 연결~~ | 만든 형식을 실제 채널에 투입 | 완료 (11-16) |
| 14 | 예산 지도 숏츠 "N억이면 서울 어느 구?": 구별 전용 59·84㎡ 중위가로 예산 구간(예: 6·9·12·15억)마다 살 수 있는 구를 이미 저장한 구 경계 지도에 색칠, 구간을 차례로 넘김. 블로그 글도 함께 | 검색·공유가 많은 '내 예산' 질문형, 기존 구별 글과 다른 각도 (11-18 콘텐츠 다양화 탐색) | 대기 (사용자 요청으로 우선) |
| 15 | 퀴즈형 "이 단지 얼마에 팔렸을까?": 단지명·면적·층·연식을 먼저 보여주고 3초 카운트다운 뒤 실거래가 공개(이번 달 거래 많은 단지, facts만 사용) | 정답 공개까지 시청 지속, 댓글 참여 유도 | 대기 (사용자 요청으로 우선) |
| 2 | 결론형 제목 + 강조 외 회색 처리: 장면 머리글을 "무엇이 결론인지" 문장으로, 막대·선은 이번 달·대상만 색, 나머지는 회색 (motion.py) | 숏폼 차트 이해도·시청 지속 | 대기 |
| 3 | 템플릿 반복 회피: 영상마다 데이터에서 뽑은 '이번 달 특이점' 1문장(최고가 경신 건수, 소형 비중 변화 등 facts 기반)과 장면 순서 변주 | YouTube '비진정성(반복) 콘텐츠' 수익화 기준 대비 | 대기 |
| 4 | 주간 "서울 전체 요약" 글과 숏츠 (구별 순위 — 막대 경주는 길어 숏폼엔 상위 5개·선 차트 위주) | 구 단위 외 검색어 확보 | 대기 |
| 5 | 단지 페이지(complex) 발행 확대와 내부 링크 강화 + 페이지마다 고유 문장 비율 확보 (템플릿 문장 60% 이상이면 애드센스 '가치 낮은 콘텐츠' 위험) | 롱테일 검색 유입, 애드센스 심사 대비 | 대기 |
| 6 | Google 서치 콘솔 등록 후 검색어·클릭 수를 성과 학습(learn.py)에 연결 → 블로그 제목·설명 개선 | 블로그 성과도 학습 고리에 포함 | 대기 (등록 필요) |
| 7 | YouTube Analytics(시청 지속률) 권한 추가 → 장면별 이탈 지점 학습 | 조회수보다 정밀한 평가 | 대기 (사용자 동의 1회 필요) |
| 8 | 무료 영상 소스(Pexels·Pixabay API) 연결 | 영상 배경 | Pixabay 완료, Pexels 키 발급 중단으로 대기 |
| 9 | 월 1회 3~5분 가로형 '서울 월간 요약' 영상 (구별 순위·타임랩스·거래량을 이어 붙임, 해설 내레이션) | 2027-02부터 YPP 진입 기준이 쇼츠 2천만 회/90일 또는 시청 8천 시간으로 올라감 → 쇼츠만으로는 수익화가 멀어 긴 영상 시청 시간 경로 확보 | 대기 (검토) |
| 10 | 3D 타임랩스 강조 구 이름표가 가려질 때 옆에 지시선(리더 라인)으로 이름 표시 | 상위 3개 구 중 이름이 안 보이는 경우 해소(11-16 샘플에서 3위 성동구 이름표 생략) | 대기 |
| 11 | 자막 시각을 음성과 정확히 맞춤: edge-tts의 단어·문장 경계 이벤트(무료, 추가 설치 없음)로 구절 시작 시각을 받고, gTTS 대체 음성일 때만 지금처럼 글자 수 비례 | 지금은 글자 수 비례라 자막이 말보다 앞서거나 늦음 → 가독성 | 대기 |
| 12 | HyperFrames(HTML→MP4) 시험: 장면 1종을 HTML·CSS로 만들어 렌더 시간·화질·Actions 동작을 비교, 좋으면 실험 변수(renderer=html)로 학습 고리에 투입 | 글꼴·레이아웃·애니메이션 표현력 향상, Claude가 HTML을 잘 다룸 | 대기 (시험) |
| 13 | FFmpeg 음량 맞춤(loudnorm, -14 LUFS 부근)과 장면 전환(xfade) | 영상마다 음량이 고르게, 플랫폼 권장 음량 | 대기 (작음) |
| 16 | 구 대결(VS): 비슷한 두 구를 중위가·거래량·신축 비중·신고가 건수 4라운드로 비교하고 라운드 승패 표시 | 같은 데이터로 새 형식, 두 구 검색어 동시 확보 | 대기 |
| 17 | '숨은 변수' 월 순환 시리즈: 층(저층·고층 가격 차), 연식(신축·구축 차), 평당가 순위, 직거래 비중, 해제(취소) 거래 비율을 한 달에 하나씩 서울 전체로 | 지금 수집 중인 칸(층·건축연도·거래유형·해제 여부)만으로 가능, 템플릿 반복 회피 | 대기 |
| 18 | 법정동 단위 순위·글: 구 안의 동별 평당가·거래량 표 | 동 이름 롱테일 검색어 | 대기 |
| 19 | 전년 같은 달 비교: 13개월치가 쌓였으니 '1년 전 같은 달보다' 비교 형식 추가(계절 영향 제거) | 전월 비교만의 단조로움 해소, 신뢰도 | 대기 |
| 20 | 전월세 자료 추가(국토교통부 아파트 전월세 실거래가 API, 같은 키·같은 요청 형식): 전세가율, 월세 비중, 전세→월세 전환 흐름 | 매매 외 두 번째 큰 주제(세입자 관심층). 공공데이터포털에서 이 API 활용신청 필요(무료, 사용자) | 대기 (11-18 활용신청 승인 완료, 기존 키 DATA_GO_KR_KEY로 호출. 엔드포인트 https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent 는 구현 때 실제 호출로 확인) |

## 구현 완료
| 날짜 | 내용 |
|---|---|
| 2026-11-17 | (사용자 요청) 3D 타임랩스 지도를 타일 도식에서 실제 구 경계로 교체: OpenStreetMap Nominatim으로 25개 구 경계를 한 번 받아 저장(ODbL, 화면·설명 출처 표기), 경계를 높이만큼 세운 입체 지도. 구 단위·삼각형 단위 정렬은 오목·가는 조각 때문에 가림 오류 → 0.2 단위 격자 칸으로 잘라 칸·조각 중심 순서로 그려 해결. 21.5초 렌더 약 2분 |
| 2026-11-16 | 3D 타임랩스 월 1회 자동 게시 연결: `timelapse3d.produce_monthly` (끝 달이 바뀌는 달에 한 편, slug `seoul-3d-YYYYMM`), 고정 틀 대본(facts의 기간·top1·low1·거래 건수만, 숫자 검사), 무료 TTS 내레이션 합성, videos 표에 넣어 기존 YouTube·Instagram·TikTok 흐름이 게시. 글이 없는 영상은 Instagram 설명 링크를 블로그 첫 화면으로. `config.toml [shorts] timelapse_monthly` 로 끄고 켬. 샘플 23.2초 렌더·프레임 확인, 테스트 1개 추가 |
| 2026-11-15 | 서울 25개 구 3D 타임랩스 렌더러 `pipeline/timelapse3d.py` (구 위치 타일 지도 + 직접 등각 투영, 12개월 재생, 카메라 회전, 상위 3개 구 강조, 가려지는 이름표 자동 생략, 21.5초). 아직 자동 게시에는 연결 안 함 → 대기열 1번 |
| 2026-11-15 | 모션 인포그래픽 렌더러(카운트업, 막대·선·순위 애니메이션, 구절 자막, 진행 막대, 테마 4종) |
| 2026-11-15 | 공개 사진 수급(위키미디어 공용, CC0/PD/CC BY만, 출처 자동 표기) |
| 2026-11-15 | 성과 수집 → 실험 가중치·교훈 → 다음 대본 반영 학습 고리 |

## 탐색 기록
(주간 작업이 날짜별로 추가: 출처 URL, 요약, 우리 콘텐츠 적용 가능성, 결정)

### 2026-11-15 (1회차)
| 분야 | 출처 | 한 줄 요약 | 적용 방법 | 결정 |
|---|---|---|---|---|
| a. Claude 스킬 | https://www.tella.com/blog/best-claude-code-skills | 인기 스킬 목록: Remotion(React 영상), 자동 줌·자막(Clipify), B-roll 찾기, frontend-design 등 | Remotion은 Node/React 스택이라 Pillow+ffmpeg 구조와 맞지 않음. '단어 단위 자막', '천천히 미는 줌(Ken Burns)' 아이디어만 참고 | 기각(설치), 아이디어는 보류 |
| a. Claude 스킬 | https://claudemarketplaces.com/skills/antvis/chart-visualization-skills/infographic-creator | 글을 인포그래픽으로 바꾸는 스킬 (AntV) | 블로그 글 요약 인포그래픽 이미지 아이디어. 외부 코드 설치 없이 기존 charts.py로 가능 | 보류 |
| b. 모션 기법 | https://onlinejournalismblog.com/2026/06/23/showing-charts-on-video-here-are-two-essential-techniques-to-make-them-effective/ | 영상 차트의 두 원칙: 단순화(상위 3~5개, 강조 외 회색, 결론형 제목, 범례 대신 직접 표기)와 움직임(내레이션에 맞춰 단계적 공개, 선은 왼→오, 막대는 위로) | 3D 타임랩스에 상위 3개 강조·직접 수치 표기 적용. 기존 장면에는 결론형 제목·회색 처리 | 채택 → 대기열 2 |
| b. 모션 기법 | https://onlinejournalismblog.com/2026/08/10/how-data-journalism-is-done-on-tiktok-six-key-takeaways-from-watching-50-videos/ | 언론사 데이터 숏폼 50편 분석: 평균 84초, 선(15)·막대(11)·지도(4) 위주, 29/33이 애니메이션, 위성사진 같은 새 시도 | 우리 길이(58초 이하)와 차트 종류는 맞음. 사람 얼굴 출연은 우리 원칙(무인)과 맞지 않아 제외 | 참고(현 방식 유지) |
| c. 코드 표현 | https://python-graph-gallery.com/342-animation-on-3d-plot | matplotlib 3D 애니메이션 예시. 3D 막대는 blit가 잘 안 되고 느림 | matplotlib 대신 회전+등각 투영을 직접 계산해 Pillow로 그림 (2배 그린 뒤 축소) | 채택(구현 완료) |
| c. 코드 표현 | https://towardsdatascience.com/how-to-make-a-gif-map-using-python-geopandas-and-matplotlib-cd8827cefbc8 | 시간 변화 지도 애니메이션은 색 범위를 전 프레임에 고정해야 함 | 타임랩스의 색·높이 기준을 12개월 전체 최댓값으로 고정 | 채택(구현 완료) |
| d. 정책 | https://www.tubefilter.com/2026/07/13/youtube-inauthentic-content-monetization-policy-update/ | 2026-07-16 YouTube 수익화 기준 명확화: 템플릿처럼 보이고 연달아 보면 반복적인 영상, 슬라이드쇼, 해설 없는 영상은 수익화 제외. AI 사용 자체는 허용 | 매일 같은 형식의 구별 숏츠는 위험 요인 → 영상마다 고유한 관찰 문장·형식 변주 | 채택 → 대기열 3 |
| d. 운영 | https://outlierkit.com/blog/youtube-updates-july-2026 | 쇼츠 맞춤 썸네일은 파트너 프로그램 채널부터 열림, 데스크톱은 3개 후보 프레임 선택. 시청자 '채널 추천 안 함' 버튼 추가 | 아직 파트너 프로그램 전이라 해당 없음. 첫 프레임이 표지이므로 첫 프레임 품질 유지(타임랩스도 첫 프레임에 막대가 보이게 함) | 보류(파트너 가입 후) |
| d. 애드센스 | https://dev.to/morinaga/why-im-betting-sentence-uniqueness-beats-page-count-for-programmatic-adsense-approval-6n1 · https://snippetcloud-ai.lovable.app/blog/adsense-approval-checklist-developers-2026 | (비공식 경험담) 자동 생성 페이지는 문장 60% 이상이 같은 틀이면 '가치 낮은 콘텐츠'로 거절되기 쉬움, 글 수보다 고유성 | 단지 페이지 확대 시 고유 문장 비율 점검 규칙 추가 | 채택 → 대기열 5 |

비고: 숏폼에서 막대 경주는 20초 이상 집중이 필요해 불리하다는 의견(출처 신뢰도 낮음)이 있어 대기열 4는 상위 5개·선 차트 위주로 바꿨다.

### 2026-11-16 (2회차)
| 분야 | 출처 | 한 줄 요약 | 적용 방법 | 결정 |
|---|---|---|---|---|
| a. Claude 스킬 | https://claudemarketplaces.com/skills/antvis/infographic/infographic-creator · https://botmonster.com/ai/epicinfographics-skill-for-claude/ | 인포그래픽 스킬이 여럿(AntV, EpicInfographics 등). 공통은 '라벨+값' 구조 데이터 → 정해진 템플릿, 'AI 티 나는' 장식 줄이기 | 새 기능은 없음. 우리 charts.py·motion.py가 이미 같은 구조. 장식 최소화 원칙만 유지 | 기각(설치), 참고 |
| b. 모션 기법 | https://advids.co/insights/visualizing-data-accurately-best-practices-for-graphs-charts-and-infographics-in-motion | 애니메이션 차트의 흔한 왜곡 두 가지: 시간 왜곡(달마다 다른 속도), 3D 공간 오용(높이 착시) | 3D 타임랩스는 달마다 같은 간격(1.5초)이고, 화면 아래에 실제 수치(상위 3개)를 숫자로 함께 표기해 높이 착시를 보완 — 현 방식 유지 | 참고(이미 반영) |
| b. 모션 기법 | https://onlinejournalismblog.com/2026/08/10/how-data-journalism-is-done-on-tiktok-six-key-takeaways-from-watching-50-videos/ | (재확인) 숏폼 데이터 영상은 선(15)·막대(11) 위주, 복잡한 차트는 드묾 | 새 형식도 선·막대 위주로 | 참고 |
| c. 코드 표현 | https://open-design.ai/skills/map-animation/ · https://talks.osgeo.org/foss4g-2026/talk/UTMSUJ/ | 지도 애니메이션 스킬(카메라 이동·경로·이름표), Noodles.gl(FOSS4G 2026) | 실제 구 경계 지도는 공개 경계 데이터 라이선스 확인이 필요 → 지금은 타일 지도 유지. 이름표 겹침 해결(지시선)은 대기열 10 | 보류 |
| d. 정책 | https://ppc.land/youtube-doubles-monetization-thresholds-and-adds-a-rolling-shorts-test/ · https://www.tubefilter.com/2026/08/10/youtube-partner-program-ad-eligibility-requirements-shorts/ | 2027-02-01부터 YPP 진입: 구독자 1,000 + 시청 8,000시간/365일 또는 쇼츠 2천만 회/90일. 쇼츠 수익 풀은 90일 1천만 회를 계속 유지해야 지급 (공식 도움말로 재확인 필요) | 쇼츠만으로 수익화는 어려움 → 월 1회 긴 영상으로 시청 시간 경로 검토 | 채택 → 대기열 9 (검토) |
| d. 블로그 SEO | https://www.digitalapplied.com/blog/programmatic-seo-after-march-2026-surviving-scaled-content-ban · https://gsqi.com/marketing-blog/august-2026-google-spam-update-case-studies/ | 2026년 3월·8월·9월 업데이트에서 '대량 생성 콘텐츠 남용'이 주요 단속 대상. AI 사용 자체가 아니라 사용자에게 가치 없는 틀 반복 페이지가 대상 (대행사 블로그, 비공식) | 대기열 5(단지 페이지 고유 문장 비율)와 3(템플릿 반복 회피)의 근거 강화. 글 수 늘리기보다 구별 고유 관찰 우선 | 기존 대기열 강화 |

비고: 3D 타임랩스 대본은 Claude를 부르지 않는 고정 틀이다. 한 달에 한 편이라 반복 위험이 낮고, 숫자 오류 가능성을 없애는 쪽을 택했다.

### 2026-11-17 (사용자 요청 검토: HyperFrames·WhisperX·FFmpeg)
| 분야 | 출처 | 한 줄 요약 | 적용 방법 | 결정 |
|---|---|---|---|---|
| c. 코드 표현 | https://github.com/heygen-com/hyperframes | HeyGen의 HTML→MP4 렌더러(Apache 2.0, 무료). 헤드리스 크롬으로 프레임을 찍고 FFmpeg로 인코딩, GSAP·CSS·Lottie·Three.js 애니메이션 사용, Claude Code용 스킬 제공 | 지금 Pillow 렌더러를 바로 갈아엎지 않고 장면 1종으로 비교 시험 | 채택(시험) → 대기열 12 |
| c. 코드 표현 | https://arxiv.org/abs/2303.00747 · https://github.com/m-bain/whisperX | Whisper 받아쓰기 + wav2vec2 강제 정렬로 단어 단위 시각을 얻음 | 우리는 대본을 이미 알고 있어 받아쓰기가 필요 없음. PyTorch·모델 내려받기로 Actions가 수 분~수십 분 느려짐. 같은 효과를 edge-tts 경계 이벤트로 무료·즉시 얻을 수 있음 | 기각 → 대안을 대기열 11 |
| c. 코드 표현 | FFmpeg | 이미 모든 영상 인코딩·음성 합치기에 사용 중(imageio-ffmpeg) | 남은 활용: 음량 맞춤·전환 효과 | 이미 사용, 보강은 대기열 13 |

### 2026-11-18 (사용자 요청: 실거래가 콘텐츠 다양화 레퍼런스)
| 분야 | 출처 | 한 줄 요약 | 적용 방법 | 결정 |
|---|---|---|---|---|
| d. 운영 | https://onlinejournalismblog.com/2026/08/10/how-data-journalism-is-done-on-tiktok-six-key-takeaways-from-watching-50-videos/ | 틱톡 데이터 저널리즘 50편 분석: 90초 이내, 같은 목소리·틀 유지, 단순 차트 하나(선·막대), 확대·강조·숫자 애니메이션, 틀 안에서 변주 | 형식을 늘리되 색·목소리·제목 틀은 통일. 복잡한 차트(누적 영역 등)는 피함 | 채택(원칙) |
| d. 운영 | https://kbthink.com/realestate/basics/blog/260917.html | KB 칼럼 "3·5·7억 예산으로 어디까지": 예산 구간별 지도 핀 + 단지 목록 + 면적·연식 기준 | 우리는 구별 중위가로 예산 구간 색칠 지도(구 경계 이미 보유) | 채택 → 대기열 14 |
| d. 운영 | https://kbthink.com/realestate/basics/blog/250729.html | 같은 예산대 단지끼리 토너먼트로 비교하는 '월드컵' 형식 | 단지 대신 구 2개 비교 VS 형식으로 응용(주관 평가 없이 숫자 라운드만) | 채택 → 대기열 16 |
| d. 운영 | https://fluxnote.io/guides/guess-the-price-video-ad-for-real-estate-agents · https://theclose.com/news/news-youtube-shorts-ideas-real-estate-agents/ | '가격 맞히기'와 주간 시장 요약이 부동산 숏폼의 대표 형식(홍보성 글이라 효과 수치는 미검증) | 실거래가 공개 퀴즈, 정답은 DB 값 | 채택 → 대기열 15 |
| d. 운영 | https://www.khan.co.kr/article/202606082020005/ · 호갱노노 '신고가' 탭 | 언론·앱은 구별 신고가 비율, 초고가 단지 사례를 자주 다룸 | 신고가는 이미 사용 중. 비율 순위는 대기열 17 순환에 포함 가능 | 참고 |
| d. 운영 | https://www.data.go.kr/data/15126474/openapi.do | 국토교통부 아파트 전월세 실거래가 상세 API(LAWD_CD·DEAL_YMD, 매매와 같은 형식). 오피스텔 매매·전월세 API도 있음 | 전월세만 우선 추가(전세가율). 오피스텔은 니치가 흐려져 보류 | 채택 → 대기열 20 |
| d. 운영 | 리치고 앱 소개, 임장 영상 흐름 | 투자점수·학군 순위, 현장 임장 영상 | 투자 점수는 투자 권유 위험, 임장은 촬영 필요, 매물 호가 비교는 사이트 약관 문제 | 기각 |

