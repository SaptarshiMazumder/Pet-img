FRAME_CATALOG_INDIA: dict[str, dict[str, any]] = {
    "Classic Wood Frame": {
        "overlay_inset": 8,
        "variants": [
            {"color": "Wooden", "preview_img_landscape": "india_frames/wooden_landscape.png", "preview_img_portrait": "india_frames/wooden_portrait.png"},
        ],
        "sizes": {
            '8" × 10"':  {"framed_base_cost": 799,  "price": 999},
            '10" × 12"': {"framed_base_cost": 999,  "price": 1299},
            '12" × 15"': {"framed_base_cost": 1299, "price": 1699},
            '15" × 19"': {"framed_base_cost": 1699, "price": 2199},
            '16" × 20"': {"framed_base_cost": 1999, "price": 2499},
            '18" × 22"': {"framed_base_cost": 2399, "price": 2999},
            '20" × 25"': {"framed_base_cost": 2999, "price": 3799},
            '24" × 30"': {"framed_base_cost": 3999, "price": 4999},
        },
    },
    "Classic Black Frame": {
        "overlay_inset": 6,
        "variants": [
            {"color": "Black", "preview_img_landscape": "india_frames/black_landscape.png", "preview_img_portrait": "india_frames/black_portrait.png"},
        ],
        "sizes": {
            '8" × 10"':  {"framed_base_cost": 799,  "price": 999},
            '10" × 12"': {"framed_base_cost": 999,  "price": 1299},
            '12" × 15"': {"framed_base_cost": 1299, "price": 1699},
            '15" × 19"': {"framed_base_cost": 1699, "price": 2199},
            '16" × 20"': {"framed_base_cost": 1999, "price": 2499},
            '18" × 22"': {"framed_base_cost": 2399, "price": 2999},
            '20" × 25"': {"framed_base_cost": 2999, "price": 3799},
            '24" × 30"': {"framed_base_cost": 3999, "price": 4999},
        },
    },
}

CATEGORY_OPTIONS_INDIA: list[str] = list(FRAME_CATALOG_INDIA.keys())


def get_available_sizes_india(category: str) -> list[str]:
    return list(FRAME_CATALOG_INDIA.get(category, {}).get("sizes", {}).keys())


def get_available_colors_india(category: str) -> list[str]:
    return [v["color"] for v in FRAME_CATALOG_INDIA.get(category, {}).get("variants", [])]


def get_framed_base_cost_india(category: str, size: str) -> int:
    return FRAME_CATALOG_INDIA.get(category, {}).get("sizes", {}).get(size, {}).get("framed_base_cost", 0)


def get_price_india(category: str, size: str) -> int:
    return FRAME_CATALOG_INDIA.get(category, {}).get("sizes", {}).get(size, {}).get("price", 0)
