# YouTube API 감사(Audit) 신청서 초안

신청 양식: https://support.google.com/youtube/contact/yt_api_form
(양식 첫 질문에서 "YouTube API Services - Audit and Quota Extension" 계열을 고릅니다.)
아래 내용을 양식 항목에 맞춰 붙여넣습니다. 양식은 영어로 작성하는 것이 일반적입니다.

---

**Organization / Developer name**: 실거래가 리포트 (individual developer)

**Contact email**: (Google 계정 이메일)

**Google Cloud project number**: 587505226594
**Project ID**: shorts-uploader-514804

**API client / OAuth client type**: Desktop (installed app), used only by the channel owner

**Website**: https://oojoaraoo-sketch.github.io/claude_ara/
**Privacy policy**: https://oojoaraoo-sketch.github.io/claude_ara/privacy/
**YouTube channel**: https://www.youtube.com/@실거래가리포트

**Which YouTube API Services do you use?**: YouTube Data API v3 — `videos.insert` only (scope `youtube.upload`)

**Describe your use case** (영문):

> This is an internal, single-user tool operated by the channel owner. Every day, a scheduled job
> (GitHub Actions) collects public apartment transaction data published by the Korean Ministry of
> Land, Infrastructure and Transport (data.go.kr), produces a short statistical summary video
> (YouTube Shorts, under 60 seconds) for a Seoul district, and uploads it to the owner's own
> channel via `videos.insert`. Each video description links to the corresponding data report on our
> website. The tool does not access, store, or display any other user's YouTube data, does not
> read analytics, comments, or subscriber data, and has no end users other than the channel owner,
> who authorized it once via OAuth. Uploads are limited to at most 2 videos per day.

**Why do you need the audit?**:

> Videos uploaded from unverified API projects are locked to private. We request an audit so that
> uploads from this project can be published publicly on the owner's own channel.

**Expected quota usage**: about 2 uploads/day × 1,600 units = ~3,200 units/day (within the default 10,000 units/day; no quota increase requested)

**Data handling**: OAuth refresh token is stored only as an encrypted GitHub Actions secret. No YouTube user data is stored or shared.

---

## 제출 전 확인할 것
- 채널에 영상이 몇 편 올라가 있으면 심사에 유리합니다 (비공개 상태여도 YouTube Studio에서 확인 가능).
- 블로그의 개인정보처리방침 페이지에 "YouTube API 서비스 이용" 문구와 Google 개인정보처리방침 링크가 있어야 합니다. → 사이트에 반영 완료.
- 심사 중 Google이 이메일로 추가 질문을 보낼 수 있습니다. 답장은 직접 해야 합니다.
