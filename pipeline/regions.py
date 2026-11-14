"""지역 코드(법정동 시군구 5자리)와 URL용 영문 슬러그."""

SEOUL = {
    "11110": ("종로구", "jongno"),
    "11140": ("중구", "jung"),
    "11170": ("용산구", "yongsan"),
    "11200": ("성동구", "seongdong"),
    "11215": ("광진구", "gwangjin"),
    "11230": ("동대문구", "dongdaemun"),
    "11260": ("중랑구", "jungnang"),
    "11290": ("성북구", "seongbuk"),
    "11305": ("강북구", "gangbuk"),
    "11320": ("도봉구", "dobong"),
    "11350": ("노원구", "nowon"),
    "11380": ("은평구", "eunpyeong"),
    "11410": ("서대문구", "seodaemun"),
    "11440": ("마포구", "mapo"),
    "11470": ("양천구", "yangcheon"),
    "11500": ("강서구", "gangseo"),
    "11530": ("구로구", "guro"),
    "11545": ("금천구", "geumcheon"),
    "11560": ("영등포구", "yeongdeungpo"),
    "11590": ("동작구", "dongjak"),
    "11620": ("관악구", "gwanak"),
    "11650": ("서초구", "seocho"),
    "11680": ("강남구", "gangnam"),
    "11710": ("송파구", "songpa"),
    "11740": ("강동구", "gangdong"),
}

GROUPS = {"seoul": ("서울", "seoul", SEOUL)}


def get_group(name: str):
    return GROUPS[name]
