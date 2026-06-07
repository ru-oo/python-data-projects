import os
import pygame

# --- 화면 설정 ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
FPS = 60
# --- 색상 정의 ---
# ==========================================
# 1. 기본 색상 & 공통 UI (General UI)
# ==========================================
BLACK = (10, 10, 12)
WHITE = (245, 245, 250)
GOLD_COLOR = (218, 165, 32)

DARK_BG = (30, 32, 36)
PANEL_BG = (45, 48, 55)         # 기본 패널 배경
ACCENT_COLOR = (70, 130, 180)   # 기본 강조 (스틸 블루)

BTN_NORMAL = (60, 65, 75)
BORDER_COLOR = (80, 85, 90)
SLOT_BG = (35, 38, 42)
PAPER_DARK = (25, 25, 30)
TOOLTIP_BG = (20, 20, 25)
POPUP_BG = (40, 40, 45)
ITEM_BG = (60, 60, 65)

# ==========================================
# 2. 텍스트 색상 (Text Colors)
# ==========================================
TXT_PRIMARY = (240, 240, 245)
TXT_SECONDARY = (160, 165, 170)
TXT_WARN = (255, 100, 100)
TXT_GOLD = (255, 215, 0)
TXT_SUCCESS = (50, 255, 50)

# ==========================================
# 3. 상태바 색상 (Status Bars)
# ==========================================
BAR_BG = (50, 50, 50)           # 상태바 배경
BAR_HP = (220, 60, 60)          # 체력 (선명한 빨강)
BAR_WATER = (60, 140, 220)      # 수분
BAR_MENTAL = (160, 80, 220)     # 멘탈
BAR_ENERGY = (255, 200, 50)     # 에너지

# ==========================================
# 4. 테마: 아포칼립스 벙커 (Bunker Theme)
# ==========================================
BUNKER_BG = (20, 18, 18)        # 아주 어두운 갈색/검정 (벽지)
BUNKER_FLOOR = (40, 35, 30)     # 어두운 나무 바닥
BUNKER_WALL_SHADOW = (10, 8, 8)
WINDOW_LIGHT = (20, 20, 35)     # 창문 밖 어두운 밤하늘
WINDOW_BAR = (60, 40, 20)       # 창문 판자

# 벙커 전용 강조색
ACCENT_RED = (180, 50, 50)      # 핏빛 레드
ACCENT_HOVER = (200, 80, 80)

# ==========================================
# 5. 테마: 쿠팡/앱 스타일 (Coupang Theme)
# ==========================================
CP_APP_BG = (242, 244, 247)     # 앱 전체 배경
CP_BG_GRAY = (245, 245, 245)    # 웹사이트/카드 배경
CP_HEADER_BG = (255, 255, 255)  # 헤더 흰색

CP_RED = (230, 20, 20)          # 쿠팡 로고 레드
CP_BLUE = (0, 116, 233)         # 로켓배송 블루
CP_GREEN = (0, 190, 160)        # 쿠팡이츠/로켓프레시 (Teal)

CP_TEXT_DARK = (50, 50, 50)
CP_TEXT_BLACK = (17, 17, 17)
CP_TEXT_GRAY = (110, 110, 110)

CP_BORDER = (221, 221, 221)
CP_SHADOW = (200, 200, 200)
CP_HEADER_WHITE = (255, 255, 255)

# === [추가] 아포칼립스 UI 테마 색상 ===
APOC_METAL_DARK = (40, 40, 35)     # 어두운 금속 바탕색
APOC_METAL_LIGHT = (80, 80, 75)    # 금속 하이라이트
APOC_RUST = (120, 60, 30)          # 녹슨 색 (테두리 등)
APOC_RUST_BRIGHT = (160, 80, 40)   # 녹슨 색 밝은 버전 (호버 시)
APOC_BOLT = (60, 60, 65)           # 나사/볼트 색상
APOC_BLOOD = (100, 20, 20)         # 핏자국 느낌 (강조)

# 색상 정의 추가 (코드 상단)
COUPANG_BLUE = (0, 174, 239)   # 쿠팡 로켓 블루
COUPANG_GREY = (245, 245, 245) # 배경용 연한 회색
DARK_GREY = (50, 50, 50)       # 텍스트용
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --- 데이터: 아이템 및 효과 ---
ITEM_ICONS_MAP = {
    # 음식
    "물": "water", "상한 두유": "soymilk", "상한 빵": "bread", "햄버거": "hamburger", "치킨": "chicken",
    "콜라": "cola", "맥주": "beer",
    
    # 도구 및 기타
    "맥북": "laptop", "롤렉스": "watch", "금괴": "gold", "한정판 피규어": "figure", 
    "총": "gun", "야구방망이": "bat", "에너지 드링크": "energy_drink",
    "생존 가이드북": "book", "건전지": "battery", "빈 박스": "box", "고장난 마우스": "mouse",
    "찢어진 택배송장": "paper", "쿠팡이츠 배달통": "delivery_bag", 
    "레트로 게임기": "gameboy", "구급상자": "medkit",
    "쿠팡플레이": "play_button", "쿠팡 쿠폰": "coupon"
}

# 음식 섭취 효과
FOOD_EFFECTS = {
    "물": {"hunger": 0, "thirst": 40, "mental": 5},
    "상한 두유": {"hunger": 30, "thirst": 30, "mental": -10},
    "상한 빵": {"hunger": 30, "thirst": -15, "mental": -10},
    "햄버거": {"hunger": 40, "thirst": 0, "mental": 5},
    "치킨": {"hunger": 50, "thirst": -15, "mental": 10},
    "콜라": {"hunger": 0, "thirst": 50, "mental": 5},
    "맥주": {"hunger": 0, "thirst": 40, "mental": 50}
}

# 사용 아이템 효과
ITEM_EFFECTS = {
    "구급상자": {"energy": 1, "hunger": 0, "thirst": 0, "mental": 50},
    # [수정] 레트로 게임기를 단순 멘탈 회복 아이템으로 변경
    "레트로 게임기": {"energy": 0, "hunger": 0, "thirst": 0, "mental": 25}, 
    "에너지 드링크": {"energy": 1, "hunger": 5, "thirst": 5, "mental": 5},
    "생존 가이드북": {"energy": 0, "hunger": 0, "thirst": 0, "mental": 15},
    "총": {"desc": "미니게임 자동 통과"},
    "야구방망이": {"desc": "미니게임 자동 통과"},
    "쿠팡 쿠폰": {"desc": "상점 50% 할인"},
}

# 아이템 분류
EFFECT_ITEMS = ["총", "야구방망이", "구급상자", "생존 가이드북", "에너지 드링크", "레트로 게임기", "쿠팡 쿠폰"]
RARE_ITEMS = ["맥북", "롤렉스", "금괴", "한정판 피규어"]
TRASH_ITEMS = ["빈 박스", "고장난 마우스", "찢어진 택배송장"]

RANDOM_EVENTS = [
    {"type": "normal", "msg": "[해킹] 누군가 계정을 털어갔습니다! (-1000point)", "money": -1000, "hunger": 0, "energy": 0, "mental": -15},
    {"type": "normal", "msg": "[습격] 바퀴벌레 떼가 식량을 덮쳤습니다! (배고픔 증가)", "money": 0, "hunger": -20, "energy": 0, "mental": -20},
    {"type": "normal", "msg": "[수신] 구조 방송이 희미하게 들립니다. (멘탈 회복)", "money": 0, "hunger": 0, "energy": 0, "mental": 20},
    {"type": "normal", "msg": "[재난] 배관이 터져 방바닥이 물바다입니다. (치우느라 행동력 감소)", "money": -500, "hunger": -5, "energy": -1, "mental": -10},
    {"type": "normal", "msg": "[발견] 구석에서 비상금을 발견했습니다! (+500point)", "money": 500, "hunger": 0, "energy": 0, "mental": 10},
    {"type": "normal", "msg": "[고통] 원인 모를 편두통이 계속됩니다. (행동력 감소)", "money": 0, "hunger": 0, "energy": -1, "mental": -10},
    {"type": "normal", "msg": "[부패] 택배 상자에서 썩은 내가 납니다. (멘탈 감소)", "money": 0, "hunger": 0, "energy": 0, "mental": -10},
    {"type": "normal", "msg": "[공포] 문 밖에서 긁는 소리가 들립니다...", "money": 0, "hunger": 0, "energy": 0, "mental": -25},
    
    {"type": "item_get", "msg": "[행운] 오배송의 행운: 문 앞에 보급 상자가 있습니다! (아이템 획득)", "money": 0, "hunger": 0, "energy": 0, "mental": 10},
    {"type": "normal", "msg": "[보상] 쿠팡 와우 보상: 적립금이 뒤늦게 들어왔습니다! (+300point)", "money": 300, "hunger": 0, "energy": 0, "mental": 5},
    {"type": "normal", "msg": "[추억] 낡은 지갑 속 가족 사진을 보며 의지를 다집니다.", "money": 0, "hunger": 0, "energy": 0, "mental": 15},
    {"type": "normal", "msg": "[생활] 찢어진 옷을 꿰맸습니다. 몸이 따뜻해집니다.", "money": 0, "hunger": 0, "energy": 0, "mental": 10},
    {"type": "normal", "msg": "[정전] 전등이 깜빡이다가 꺼졌습니다. 어둠이 깔립니다.", "money": 0, "hunger": 0, "energy": 0, "mental": -20},
    {"type": "normal", "msg": "[파손] 방바닥에 금이 가기 시작했습니다. (보수비용 발생, 힘듦)", "money": -300, "hunger": -5, "energy": -1, "mental": -5},
    {"type": "item_lose", "msg": "[손실] 쥐가 가방을 갉아 아이템 하나를 물어갔습니다!", "money": 0, "hunger": 0, "energy": 0, "mental": -10}
]

WORDS_DATA = ["Survival", "Zombie", "Infected", "Home", "Supply", "Danger", "Weapon", "Water", "Food", "Emergency", "Hazard", "Outbreak", "Virus", "Silence", "Run"]

def get_font(size, bold=False):
    custom_fonts = ["survival_font.ttf", "font/survival_font.ttf"]
    for font_path in custom_fonts:
        if os.path.exists(font_path):
            try: 
                # [수정] 폰트 객체 생성 후 bold 옵션 적용
                font = pygame.font.Font(font_path, size)
                if bold: 
                    font.set_bold(True) 
                return font
            except: pass
            
    font_name = "malgungothic" if os.name == 'nt' else "AppleGothic"
    try: return pygame.font.SysFont(font_name, size, bold=bold)
    except: return pygame.font.SysFont(None, size, bold=bold)
