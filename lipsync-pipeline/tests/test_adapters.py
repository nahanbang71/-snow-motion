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


# ------------------------------------------------------------ InfiniteTalk
def _it_req(tmp_path, **opt):
    m = get_lipsync_model("infinitetalk")
    return m, LipSyncRequest(tmp_path / "input.mp4", tmp_path / "audio.wav", tmp_path / "out.mp4", 24.0, m.resolve(GenerationOptions(seed=7, **opt)))


def test_infinitetalk_command_matches_official_cli(tmp_path):
    m, req = _it_req(tmp_path)
    cmd = m.build_command(req, tmp_path / "in.json", tmp_path / "result", tmp_path / "emb", 300)
    assert cmd[1] == "generate_infinitetalk.py" and "-m" not in cmd[:2]                    # 모듈 실행이 아니라 스크립트 실행
    get = lambda k: cmd[cmd.index(k) + 1]
    assert get("--ckpt_dir") == "weights/Wan2.1-I2V-14B-480P" and get("--wav2vec_dir") == "weights/chinese-wav2vec2-base"
    assert get("--infinitetalk_dir") == "weights/InfiniteTalk/single/infinitetalk.safetensors"
    assert get("--sample_steps") == "40" and get("--sample_text_guide_scale") == "5.0" and get("--base_seed") == "7"
    assert get("--mode") == "streaming" and get("--size") == "infinitetalk-720" and get("--max_frame_num") == "1000"
    assert get("--offload_model") == "False" and "--num_persistent_param_in_dit" not in cmd
    assert "--input_json" in cmd and "--cond_video" not in cmd and "--steps" not in cmd


def test_infinitetalk_offload_modes_and_long_segments(tmp_path):
    m, model = _it_req(tmp_path, offload="model")
    cmd = m.build_command(model, tmp_path / "i.json", tmp_path / "r", tmp_path / "e", 1500)
    assert cmd[cmd.index("--offload_model") + 1] == "True" and "--num_persistent_param_in_dit" not in cmd and cmd[cmd.index("--max_frame_num") + 1] == "1500"
    m, seq = _it_req(tmp_path, offload="sequential")
    cmd = m.build_command(seq, tmp_path / "i.json", tmp_path / "r", tmp_path / "e")
    assert cmd[cmd.index("--num_persistent_param_in_dit") + 1] == "0" and cmd[cmd.index("--offload_model") + 1] == "True"
    m, bad = _it_req(tmp_path, extra={"size": "infinitetalk-1080"})
    with pytest.raises(PipelineError, match="--size"):
        m.build_command(bad, tmp_path / "i.json", tmp_path / "r", tmp_path / "e")


def test_infinitetalk_input_json_and_output_rule(tmp_path):
    import json as _json
    m = get_lipsync_model("infinitetalk")
    data = _json.loads(m.build_input_json(Path("/t/내 폴더/input.mp4"), Path("/t/내 폴더/audio.wav")))
    assert set(data) == {"prompt", "cond_video", "cond_audio"} and data["cond_audio"] == {"person1": "/t/내 폴더/audio.wav"}
    assert m.expected_output(Path("/r/result")) == Path("/r/result.mp4")                    # --save_file 는 확장자 없는 접두사
    from lipsync_pipeline.models import infinitetalk as it
    assert it.FPS == 25 and ("MeiGen-AI/InfiniteTalk", [], "weights/InfiniteTalk", None) in it.WEIGHT_DOWNLOADS


def test_infinitetalk_generate_with_fake_tool_resizes_to_input(tmp_path, monkeypatch):
    import json as _json
    import subprocess
    from lipsync_pipeline.utils import video_stream_info
    repo = tmp_path / "InfiniteTalk"
    for d in ("weights/Wan2.1-I2V-14B-480P", "weights/chinese-wav2vec2-base", "weights/InfiniteTalk/single"):
        (repo / d).mkdir(parents=True)
    (repo / "weights/InfiniteTalk/single/infinitetalk.safetensors").write_text("x")
    (repo / "generate_infinitetalk.py").write_text(
        "import argparse, json, subprocess\n"
        "p = argparse.ArgumentParser()\n"
        "for k in ('--input_json', '--save_file'): p.add_argument(k)\n"
        "a, _ = p.parse_known_args()\n"
        "d = json.load(open(a.input_json)); assert d['cond_audio']['person1'].endswith('audio.wav')\n"
        "subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=size=640x640:rate=25:duration=1', '-pix_fmt', 'yuv420p', a.save_file + '.mp4'], check=True)\n")
    monkeypatch.setenv("INFINITETALK_DIR", str(repo))
    src = tmp_path / "input.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=512x512:rate=24:duration=1", "-pix_fmt", "yuv420p", str(src)], check=True)
    (tmp_path / "audio.wav").write_bytes(b"RIFF")
    m = get_lipsync_model("infinitetalk")
    req = LipSyncRequest(src, tmp_path / "audio.wav", tmp_path / "out.mp4", 24.0, m.resolve(GenerationOptions()))
    m.check_environment(req.options)
    m.generate(req)
    v = video_stream_info(tmp_path / "out.mp4")
    assert (v["width"], v["height"]) == (512, 512)                                           # 640x640 버킷 출력을 입력 해상도로
