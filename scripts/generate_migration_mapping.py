#!/usr/bin/env python3
"""
產生遷移對應表 - 將 utils.py 函數映射至新模組位置

根據函數名稱、職責、依賴關係,自動產生遷移對應表
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List


# 遷移規則: 函數名稱模式 → 目標模組
MIGRATION_RULES = {
    # Domain Layer - 純邏輯
    "domain/layout.py": [
        "_normalize_letters_sequence",
        "_plan_letter_images",
        "_letter_asset_filename",
        "_letters_missing_names",
        "_layout_zhuyin_column",
    ],
    "domain/typography.py": [
        # 已遷移: _zhuyin_main_gap, zhuyin_for
    ],
    "domain/effects.py": [
        "_progress_bar_band_layout",
        "_progress_bar_base_arrays",
        "_make_progress_bar_mask",
        "_build_progress_bar_segments",
        "_apply_fadeout",
        "_apply_fadein",
    ],
    "domain/timing.py": [
        "_coerce_non_negative_float",
        "_coerce_bool",
    ],

    # Infrastructure Layer - 框架整合
    "infrastructure/rendering/pillow_adapter.py": [
        "_make_text_imageclip",  # 包含內部 _SimpleImageClip 類別
        "_measure_text_with_pil",
        "_find_system_font",
        # _SimpleImageClip 內部方法 (不需單獨映射):
        # "__init__", "get_frame", "with_duration", "duration", "make_frame"
    ],
    "infrastructure/video/moviepy_adapter.py": [
        "_make_fixed_letter_clip",
        "_ensure_dimensions",
        "_ensure_fullscreen_cover",
        "_auto_letterbox_crop",
        "_create_placeholder_mp4_with_ffmpeg",
    ],
    "infrastructure/media/ffmpeg_wrapper.py": [
        "_probe_media_duration",
        "_find_and_set_ffmpeg",
    ],
    "infrastructure/media/audio.py": [
        "make_beep",
        "synthesize_beeps",
    ],

    # Application Layer - 業務邏輯
    "application/video_service.py": [
        "_resolve_entry_video_path",
        "_is_entry_enabled",
        "_prepare_entry_context",
        "_resolve_ending_video_path",
        "_is_ending_enabled",
        "_prepare_ending_context",
        "_resolve_letter_asset_dir",
        "_prepare_letters_context",
        "_log_missing_letter_assets",
        "render_video_moviepy",
        "render_video_stub",
        "concatenate_videos_with_transitions",
    ],

    # Shared Layer - 共用工具
    "shared/validation.py": [
        # 已遷移: load_json, validate_schema
    ],
}


def load_migration_status(status_path: Path) -> Dict:
    """載入遷移狀態報告"""
    with open(status_path, encoding="utf-8") as f:
        return json.load(f)


def generate_migration_mapping(
    migration_status: Dict, rules: Dict[str, List[str]]
) -> List[Dict]:
    """產生遷移對應表"""

    mapping = []

    # 需要遷移的函數
    functions_to_migrate = {
        func["function_name"]: func for func in migration_status["in_utils_only"]
    }

    # 根據規則生成對應
    for target_module, func_patterns in rules.items():
        for func_name in func_patterns:
            if func_name in functions_to_migrate:
                func_info = functions_to_migrate[func_name]

                mapping.append({
                    "function_name": func_name,
                    "old_location": "spellvid/utils.py",
                    "new_location": f"spellvid/{target_module}",
                    "category": func_info["category"],
                    "call_count": func_info["call_count"],
                    "wrapper_needed": False,  # 大部分不需要 wrapper
                    "migration_priority": _calculate_priority(func_name, func_info),
                    "dependencies": [],  # 稍後手動填充
                    "notes": "",
                })

    # 識別未映射的函數
    mapped_funcs = {item["function_name"] for item in mapping}
    unmapped = [
        func_name
        for func_name in functions_to_migrate.keys()
        if func_name not in mapped_funcs
    ]

    if unmapped:
        print(f"\n⚠️  未映射的函數 ({len(unmapped)} 個):")
        for func_name in unmapped:
            print(f"  - {func_name}")

    return mapping


def _calculate_priority(func_name: str, func_info: Dict) -> str:
    """計算遷移優先級"""
    call_count = func_info["call_count"]

    # 高引用數 = 高優先級
    if call_count >= 10:
        return "high"
    elif call_count >= 5:
        return "medium"
    else:
        return "low"


def main():
    parser = argparse.ArgumentParser(description="產生遷移對應表")
    parser.add_argument(
        "--status",
        default="specs/004-complete-module-migration/MIGRATION_STATUS.json",
        help="遷移狀態報告路徑",
    )
    parser.add_argument(
        "--output",
        default="specs/004-complete-module-migration/MIGRATION_MAPPING.json",
        help="輸出遷移對應表",
    )

    args = parser.parse_args()

    print("📋 產生遷移對應表")
    print("=" * 60)

    # 載入遷移狀態
    print("\nStep 1: 載入遷移狀態...")
    status_path = Path(args.status)
    migration_status = load_migration_status(status_path)
    print(f"  需遷移: {len(migration_status['in_utils_only'])} 個函數")

    # 產生對應表
    print("\nStep 2: 套用遷移規則...")
    mapping = generate_migration_mapping(migration_status, MIGRATION_RULES)
    print(f"  已映射: {len(mapping)} 個函數")

    # 按目標模組分組統計
    print("\nStep 3: 目標模組分布:")
    by_module = {}
    for item in mapping:
        module = item["new_location"]
        by_module[module] = by_module.get(module, 0) + 1

    for module, count in sorted(by_module.items()):
        print(f"  {module}: {count} 個")

    # 優先級統計
    print("\nStep 4: 優先級分布:")
    by_priority = {}
    for item in mapping:
        priority = item["migration_priority"]
        by_priority[priority] = by_priority.get(priority, 0) + 1

    for priority, count in sorted(by_priority.items()):
        print(f"  {priority}: {count} 個")

    # 輸出 JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 遷移對應表已儲存: {output_path}")
    print(f"📄 總計: {len(mapping)} 個函數映射")

    # 遷移建議
    print("\n💡 遷移建議:")
    print("  1. 高優先級函數 (call_count ≥ 10) 先遷移")
    print("  2. 按模組分批遷移 (domain → infrastructure → application)")
    print("  3. 遷移後執行測試驗證")


if __name__ == "__main__":
    main()
