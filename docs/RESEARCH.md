# 탐색·개선 기록 (주간 예약 작업 "콘텐츠 고도화 탐색"이 갱신)

> 매주 탐색한 것(인기 Claude 스킬, 모션 인포그래픽 기법, Claude로 만드는 새 표현, 채널 성장 방법)을 기록하고,
> 쓸 만한 것은 아래 대기열에 넣어 한 주에 하나씩 구현한다. 외부 코드는 그대로 설치·실행하지 않고, 읽고 이해한 뒤 직접 구현한다.

## 대기열 (위에서부터 구현)
| # | 아이디어 | 기대 효과 | 상태 |
|---|---|---|---|
| 1 | 3D 타임랩스 월 1회 자동 게시 연결: 매월 초 run.py에서 렌더 → 대본(facts의 top1/low1만 사용)·음성·제목·설명 → YouTube·Instagram·TikTok 대기열 | 만든 형식을 실제 채널에 투입 | 대기 |
| 2 | 결론형 제목 + 강조 외 회색 처리: 장면 머리글을 "무엇이 결론인지" 문장으로, 막대·선은 이번 달·대상만 색, 나머지는 회색 (motion.py) | 숏폼 차트 이해도·시청 지속 | 대기 |
| 3 | 템플릿 반복 회피: 영상마다 데이터에서 뽑은 '이번 달 특이점' 1문장(최고가 경신 건수, 소형 비중 변화 등 facts 기반)과 장면 순서 변주 | YouTube '비진정성(반복) 콘텐츠' 수익화 기준 대비 | 대기 |
| 4 | 주간 "서울 전체 요약" 글과 숏츠 (구별 순위 — 막대 경주는 길어 숏폼엔 상위 5개·선 차트 위주) | 구 단위 외 검색어 확보 | 대기 |
| 5 | 단지 페이지(complex) 발행 확대와 내부 링크 강화 + 페이지마다 고유 문장 비율 확보 (템플릿 문장 60% 이상이면 애드센스 '가치 낮은 콘텐츠' 위험) | 롱테일 검색 유입, 애드센스 심사 대비 | 대기 |
| 6 | Google 서치 콘솔 등록 후 검색어·클릭 수를 성과 학습(learn.py)에 연결 → 블로그 제목·설명 개선 | 블로그 성과도 학습 고리에 포함 | 대기 (등록 필요) |
| 7 | YouTube Analytics(시청 지속률) 권한 추가 → 장면별 이탈 지점 학습 | 조회수보다 정밀한 평가 | 대기 (사용자 동의 1회 필요) |
| 8 | 무료 영상 소스(Pexels·Pixabay API) 연결 | 영상 배경 | 대기 (무료 가입 필요) |

## 구현 완료
| 날짜 | 내용 |
|---|---|
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
