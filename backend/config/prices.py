FRAME_CATALOG: dict[str, dict[str, any]] = {
    "油絵額縁 8235(Oil painting frame 8235)": {
        "variants": [
            {"color": "ホワイト",  "preview_img": "backend/config/config_preview_images/8235_white.jpg"},
            {"color": "ブラック",  "preview_img": "backend/config/config_preview_images/8235_black.jpg"},
        ],
        "sizes": {
            "158×228(SM)":  {"framed_base_cost": 3465,  "price": 4300},   # confirmed
            "220×273(F3)":  {"framed_base_cost": 4119,  "price": 5100},   # confirmed
            "242×333(F4)":  {"framed_base_cost": 4581,  "price": 5700},   # confirmed
            "318×409(F6)":  {"framed_base_cost": 5236,  "price": 6500},   # confirmed
            "379×455(F8)":  {"framed_base_cost": 6400,  "price": 8000},   # estimated
            "455×530(F10)": {"framed_base_cost": 8085,  "price": 10100},  # confirmed
            "530×651(F15)": {"framed_base_cost": 10200, "price": 12800},  # estimated
        },
    },
    "油絵額縁 8117(Oil painting frame 8117)": {
        "variants": [
            {"color": "ストーングレー", "preview_img": "backend/config/config_preview_images/8117_stone.jpg"},
        ],
        "sizes": {
            "158×228(SM)":  {"framed_base_cost": 5236,  "price": 6500},
            "220×273(F3)":  {"framed_base_cost": 6160,  "price": 7700},
            "242×333(F4)":  {"framed_base_cost": 7007,  "price": 8800},
            "318×409(F6)":  {"framed_base_cost": 8239,  "price": 10300},
            "379×455(F8)":  {"framed_base_cost": 10318, "price": 12900},
            "455×530(F10)": {"framed_base_cost": 12012, "price": 15000},
            "530×651(F15)": {"framed_base_cost": 19481, "price": 24400},
        },
    },
    "油絵額縁 レインボー(Oil painting frame, Rainbow)": {
        "variants": [
            {"color": "金 (Gold)",    "preview_img": "backend/config/config_preview_images/rainbow_gold.jpg"},
            {"color": "銀 (Silver)",  "preview_img": "backend/config/config_preview_images/rainbow_silver.jpg"},
        ],
        "sizes": {
            "158x228 (SM)": {"framed_base_cost": 7623,  "price": 9500},
            "220×273(F3)":  {"framed_base_cost": 8624,  "price": 10800},
            "242×333(F4)":  {"framed_base_cost": 9317,  "price": 11600},
            "318×409(F6)":  {"framed_base_cost": 10703, "price": 13400},
            "379×455(F8)":  {"framed_base_cost": 13090, "price": 16400},
            "455×530(F10)": {"framed_base_cost": 16786, "price": 21000},
            "530×651(F15)": {"framed_base_cost": 22099, "price": 27600},
        },
    }
}

CATEGORY_OPTIONS: list[str] = list(FRAME_CATALOG.keys())


def get_available_sizes(category: str) -> list[str]:
    return list(FRAME_CATALOG.get(category, {}).get("sizes", {}).keys())


def get_available_colors(category: str) -> list[str]:
    return [v["color"] for v in FRAME_CATALOG.get(category, {}).get("variants", [])]


def get_framed_base_cost(category: str, size: str) -> int:
    return FRAME_CATALOG.get(category, {}).get("sizes", {}).get(size, {}).get("framed_base_cost", 0)


def get_price(category: str, size: str) -> int:
    return FRAME_CATALOG.get(category, {}).get("sizes", {}).get(size, {}).get("price", 0)
