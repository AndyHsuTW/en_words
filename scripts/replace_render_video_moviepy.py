"""Replace render_video_moviepy with deprecated wrapper."""

# Read file
with open('spellvid/utils.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find render_video_moviepy start (line 1310, 0-indexed = 1309)
start_line = 1309

# New wrapper code
new_wrapper = '''def render_video_moviepy(
    item: Dict[str, Any],
    out_path: str,
    dry_run: bool = False,
    skip_ending: bool = False,
) -> Dict[str, Any]:
    """⚠️ DEPRECATED: 向後相容層 - 將在 v2.0 移除

    使用 application.video_service.render_video 代替

    Args:
        item: JSON configuration dict
        out_path: Output MP4 file path
        dry_run: If True, only compute metadata without rendering
        skip_ending: If True, omit ending video (for batch processing)

    Returns:
        Rendering result dict (legacy format for compatibility)

    Example:
        >>> item = {"letters": "C c", "word_en": "Cat", "word_zh": "貓"}
        >>> render_video_moviepy(item, "out/cat.mp4")  # doctest: +SKIP
        DeprecationWarning: render_video_moviepy is deprecated...
    """
    warnings.warn(
        "render_video_moviepy is deprecated. "
        "Use application.video_service.render_video instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from spellvid.application.video_service import render_video
    
    # Delegate to new API
    result = render_video(item, out_path, dry_run, skip_ending)
    
    # Convert new format to legacy format for backward compatibility
    return {
        "status": "ok",
        "out": out_path,
        "total_duration_sec": result.get("duration", 0.0),
        "metadata": result.get("metadata", {}),
    }


'''

# Replace lines 1310-2940 (0-indexed: 1309-2940) with new wrapper
# Keep everything before, insert wrapper, keep everything after line 2940
new_lines = lines[:start_line] + [new_wrapper] + lines[2941:]

# Write back
with open('spellvid/utils.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Replaced render_video_moviepy with deprecated wrapper')
print(f'Original: {len(lines)} lines')
print(f'New: {len(new_lines)} lines')
print(f'Removed: {len(lines) - len(new_lines)} lines')
