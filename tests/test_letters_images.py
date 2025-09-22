import os
import pytest

from spellvid import utils


def test_letters_image_plan_uses_assets(letter_assets_dir):
    item = {
        "letters": "I i",
        "word_en": "Ice",
        "word_zh": "冰",
        "image_path": "",
        "music_path": "",
        "letters_as_image": True,
    }
    boxes = utils.compute_layout_bboxes(item)
    letters_box = boxes.get("letters")
    assert letters_box is not None
    assert letters_box.get("mode") == "image"
    assert letters_box.get("w") == 838
    assert letters_box.get("h") == 440
    assert letters_box.get('missing') == []
    assert letters_box.get('x') == 0
    assert letters_box.get('y') == utils.LETTER_SAFE_Y
    assert letters_box.get('gap') == utils.LETTER_BASE_GAP * utils.LETTER_EXTRA_SCALE

    plan = utils._plan_letter_images(item["letters"], str(letter_assets_dir))
    filenames = [entry["filename"] for entry in plan["letters"]]
    assert filenames == ["I.png", "i_small.png"]
    widths = [entry["width"] for entry in plan["letters"]]
    heights = [entry["height"] for entry in plan["letters"]]
    xs = [entry["x"] for entry in plan["letters"]]
    assert widths == [440, 384]
    assert heights == [440, 384]
    assert xs[0] == -64
    assert xs[1] == 454
    assert plan["gap"] == int(utils.LETTER_BASE_GAP * utils.LETTER_EXTRA_SCALE)
    assert plan["bbox"]["w"] == 838
    assert plan["bbox"]["h"] == 440
    assert plan["bbox"].get("x_offset") == -64


def test_letters_missing_assets_reported_in_dry_run(tmp_path, monkeypatch, capsys):
    empty_assets = tmp_path / "letters"
    empty_assets.mkdir()
    monkeypatch.setenv("SPELLVID_LETTER_ASSET_DIR", str(empty_assets))
    out_path = tmp_path / "sample.mp4"
    item = {
        "letters": "Z z",
        "word_en": "Zoo",
        "word_zh": "動物園",
        "image_path": "",
        "music_path": "",
        "letters_as_image": True,
    }

    res = utils.render_video_stub(item, str(out_path), dry_run=True)
    captured = capsys.readouterr()
    assert "WARNING: letters asset missing" in captured.out
    missing = res.get("letters_missing")
    assert missing is not None
    assert "Z.png" in missing
    assert "z_small.png" in missing
    assert res.get("letters_mode") == "image"
    assert res.get("letters_layout") == []


def test_letters_text_mode_fallback(tmp_path):
    item = {
        "letters": "Hi",
        "word_en": "Hi",
        "word_zh": "嗨",
        "image_path": "",
        "music_path": "",
        "letters_as_image": False,
    }
    boxes = utils.compute_layout_bboxes(item)
    letters_box = boxes.get("letters")
    assert letters_box is not None
    assert letters_box.get("mode") == "text"
    res = utils.render_video_stub(item, str(tmp_path / "text.mp4"), dry_run=True)
    assert res.get("letters_mode") == "text"
    assert res.get("letters_missing") == []

