"""외부 모델 어댑터의 '명령 조립/설정 형식/출력 경로 규칙' 검증 (실제 모델은 실행하지 않는다).
기대값은 각 공식 저장소의 실제 코드를 읽고 확인한 내용이다 (근거는 각 어댑터 파일 상단 주석)."""
import json
from pathlib import Path

import pytest

from lipsync_pipeline.models import GenerationOptions, LipSyncRequest, get_lipsync_model
from lipsync_pipeline.models import musetalk as mt
from lipsync_pipeline.utils import PipelineError


def _req(tmp_path, **opt):
    m = get_lipsync_model("musetalk")
    o = m.resolve(GenerationOptions(**opt))
    return m, LipSyncRequest(tmp_path / "a" / "input.mp4", tmp_path / "a" / "audio.wav", tmp_path / "out.mp4", 24.0, o)


# ------------------------------------------------------------ MuseTalk
def test_musetalk_command_matches_official_cli(tmp_path):
    m, req = _req(tmp_path, precision="fp16")
    cmd = m.build_command(req, tmp_path / "inference.yaml", tmp_path / "result")
    assert cmd[1:3] == ["-m", "scripts.inference"]
    assert cmd[cmd.index("--unet_model_path") + 1] == "models/musetalkV15/unet.pth"
    assert cmd[cmd.index("--unet_config") + 1] == "models/musetalkV15/musetalk.json"      # 기본값(models/musetalk/config.json)과 다름
    assert cmd[cmd.index("--version") + 1] == "v15" and "--use_float16" in cmd
    assert cmd[cmd.index("--inference_config") + 1] == str(tmp_path / "inference.yaml")
    assert "--steps" not in cmd and "--seed" not in cmd                                   # 해당 인자가 없는 모델
    _, req32 = _req(tmp_path, precision="fp32")
    assert "--use_float16" not in m.build_command(req32, tmp_path / "c.yaml", tmp_path / "r")   # 품질 우선: 플래그 없음
    _, reqbf = _req(tmp_path, precision="bf16")
    with pytest.raises(PipelineError, match="bf16"):
        m.build_command(reqbf, tmp_path / "c.yaml", tmp_path / "r")


def test_musetalk_extra_flags_are_whitelisted(tmp_path):
    m, req = _req(tmp_path, extra={"batch_size": 2, "extra_margin": 12})
    cmd = m.build_command(req, tmp_path / "c.yaml", tmp_path / "r")
    assert cmd[cmd.index("--batch_size") + 1] == "2" and cmd[cmd.index("--extra_margin") + 1] == "12"
    _, bad = _req(tmp_path, extra={"rm_rf": 1})
    with pytest.raises(PipelineError, match="지원하지 않는"):
        m.build_command(bad, tmp_path / "c.yaml", tmp_path / "r")


def test_musetalk_config_format_and_output_rule(tmp_path):
    import yaml
    m = get_lipsync_model("musetalk")
    cfg = yaml.safe_load(m.build_config(Path("/tmp/x/input.mp4"), Path("/tmp/x/audio.wav")))
    assert cfg == {"task_0": {"video_path": "/tmp/x/input.mp4", "audio_path": "/tmp/x/audio.wav", "result_name": "take.mp4"}}
    assert m.expected_output(Path("/r")) == Path("/r/v15/take.mp4")                        # <result_dir>/<version>/<result_name>


def test_musetalk_rejects_paths_that_break_its_unquoted_shell_commands(tmp_path):
    m = get_lipsync_model("musetalk")
    m.check_shell_safe(tmp_path / "ok" / "input.mp4")
    with pytest.raises(PipelineError, match="공백"):
        m.check_shell_safe(Path("/work/내 영상/input.mp4"))


def test_musetalk_weight_list_matches_official_download_script():
    files = {f for _, fs, _ in mt.WEIGHT_DOWNLOADS for f in fs}
    assert {"musetalkV15/unet.pth", "musetalkV15/musetalk.json", "dw-ll_ucoco_384.pth", "latentsync_syncnet.pt"} <= files
    assert all(not any(a.startswith("--") for a in fs) for _, fs, _ in mt.WEIGHT_DOWNLOADS)   # hf download: 파일명만 (--exclude 금지)


def test_musetalk_generate_end_to_end_with_fake_tool(tmp_path, monkeypatch):
    """가짜 scripts.inference 가 공식 출력 규칙(<result_dir>/v15/<result_name>)대로 파일을 만들면 어댑터가 가져온다."""
    repo = tmp_path / "MuseTalk"; (repo / "models/musetalkV15").mkdir(parents=True); (repo / "models/whisper").mkdir(parents=True)
    for f in ("models/musetalkV15/unet.pth", "models/musetalkV15/musetalk.json", "models/whisper/config.json"):
        (repo / f).write_text("x")
    (repo / "scripts").mkdir(); (repo / "scripts/__init__.py").write_text("")
    (repo / "scripts/inference.py").write_text(
        "import argparse, os, yaml\n"
        "p = argparse.ArgumentParser(); p.add_argument('--inference_config'); p.add_argument('--result_dir')\n"
        "a, _ = p.parse_known_args()\n"
        "cfg = yaml.safe_load(open(a.inference_config))['task_0']\n"
        "assert ' ' not in cfg['video_path'] and os.path.isfile(cfg['video_path']) and os.path.isfile(cfg['audio_path'])\n"
        "out = os.path.join(a.result_dir, 'v15', cfg['result_name']); os.makedirs(os.path.dirname(out), exist_ok=True)\n"
        "open(out, 'wb').write(open(cfg['video_path'], 'rb').read())\n")
    monkeypatch.setenv("MUSETALK_DIR", str(repo))
    d = tmp_path / "내 폴더 공백"; d.mkdir()
    (d / "input.mp4").write_bytes(b"VIDEO"); (d / "audio.wav").write_bytes(b"AUDIO")
    m = get_lipsync_model("musetalk")
    req = LipSyncRequest(d / "input.mp4", d / "audio.wav", d / "out.mp4", 24.0, m.resolve(GenerationOptions()))
    m.check_environment(req.options)
    assert m.generate(req) == d / "out.mp4" and (d / "out.mp4").read_bytes() == b"VIDEO"


def test_musetalk_swallowed_error_is_reported_from_missing_output(tmp_path, monkeypatch):
    repo = tmp_path / "MuseTalk"; (repo / "scripts").mkdir(parents=True); (repo / "scripts/__init__.py").write_text("")
    (repo / "scripts/inference.py").write_text("print('Error occurred during processing: boom')\n")   # 종료 코드 0
    monkeypatch.setenv("MUSETALK_DIR", str(repo))
    m = get_lipsync_model("musetalk")
    req = LipSyncRequest(tmp_path / "i.mp4", tmp_path / "a.wav", tmp_path / "o.mp4", 24.0, m.resolve(GenerationOptions()))
    (tmp_path / "i.mp4").write_bytes(b"v"); (tmp_path / "a.wav").write_bytes(b"a")
    with pytest.raises(PipelineError, match="boom"):
        m.generate(req)
