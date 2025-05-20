# agent/modules/plan/available_test.py

# 🎮 행동 가능한 액션 목록
VALID_ACTIONS = {"eat", "use", "break", "offer", "find"}

# 🗺 지역 정보 (Location -> [Object])
REGION_LOCATION_OBJECTS = {
    "house": ["Bed", "Bookshelf", "Desk", "Telescope", "Piano"],
    "square": ["Wilson"],
    "temple": ["Candle"],
    "mountain": ["Strawberry", "Tree", "Rock", "Flower", "Mushroom"],
    "forest": ["Apple", "Grape", "Tree", "Flower", "Mushroom"],
    "plain": ["Banana", "Tree", "Flower"],
    "beach": [
        "Coconut", "BigFish", "SmallFish", "Egg",
        "Rock", "Shell", "Conch", "Fishing Rod"
    ]
}


# 🎯 find에서 위치 무관하게 찾을 수 있는 오브젝트
FINDABLE_ANYWHERE = {"Jewel", "Letter", "Book"}

# 🔍 find 유효성 검사용 - 특정 오브젝트가 실제로 등장 가능한 위치
OBJECT_LOCATION_MAP = {
    "Banana": ["plain"],
    "Apple": ["forest"],
    "Grape": ["forest"],
    "Coconut": ["beach"],
    "Strawberry": ["mountain"],
    "Mushroom": ["forest", "mountain"],
    "Tree": ["mountain", "forest", "plain"],
    "Rock": ["mountain", "beach"],
    "Flower": ["town", "forest", "mountain"],
    "Shell": ["beach"],
    "Conch": ["beach"],
    "Egg": ["beach"],
    "BigFish": ["beach"],
    "SmallFish": ["beach"],
}
