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
    t = cfg["task_0"]      # Windows 는 경로 구분자가 \ 라서 문자열이 아니라 Path 로 비교한다
    assert set(cfg) == {"task_0"} and set(t) == {"video_path", "audio_path", "result_name"}
    assert Path(t["video_path"]) == Path("/tmp/x/input.mp4") and Path(t["audio_path"]) == Path("/tmp/x/audio.wav")
    assert t["result_name"] == "take.mp4"
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
    assert set(data) == {"prompt", "cond_video", "cond_audio"}
    assert set(data["cond_audio"]) == {"person1"} and Path(data["cond_audio"]["person1"]) == Path("/t/내 폴더/audio.wav")   # Windows 경로 구분자 대응
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


# ------------------------------------------------------------ Wan2.2-S2V
def _wan_req(tmp_path, **opt):
    m = get_lipsync_model("wan_s2v")
    return m, LipSyncRequest(tmp_path / "input.mp4", tmp_path / "audio.wav", tmp_path / "out.mp4", 24.0, m.resolve(GenerationOptions(seed=11, **opt)))


def test_wan_s2v_command_matches_official_cli(tmp_path):
    m, req = _wan_req(tmp_path)
    cmd = m.build_command(req, tmp_path / "ref.png", tmp_path / "result.mp4")
    get = lambda k: cmd[cmd.index(k) + 1]
    assert cmd[1] == "generate.py" and get("--task") == "s2v-14B" and get("--ckpt_dir") == "Wan2.2-S2V-14B"
    # 예제 기본값(고양이 프롬프트/예제 이미지/예제 오디오)으로 조용히 채워지지 않도록 항상 명시한다
    assert get("--prompt") == "a person is singing" and get("--image") == str(tmp_path / "ref.png") and get("--audio") == str(tmp_path / "audio.wav")
    assert get("--save_file") == str(tmp_path / "result.mp4")                                 # 확장자 포함 전체 파일명
    assert get("--sample_steps") == "40" and get("--sample_guide_scale") == "4.5" and get("--base_seed") == "11"
    assert get("--size") == "1280*720" and "--start_from_ref" in cmd
    assert get("--offload_model") == "False" and "--convert_model_dtype" not in cmd and "--t5_cpu" not in cmd
    assert "--pose_video" not in cmd and "--enable_tts" not in cmd


def test_wan_s2v_offload_modes_and_validation(tmp_path):
    m, a = _wan_req(tmp_path, offload="model")
    cmd = m.build_command(a, tmp_path / "r.png", tmp_path / "o.mp4")
    assert cmd[cmd.index("--offload_model") + 1] == "True" and "--convert_model_dtype" in cmd and "--t5_cpu" not in cmd
    m, b = _wan_req(tmp_path, offload="sequential")
    cmd = m.build_command(b, tmp_path / "r.png", tmp_path / "o.mp4")
    assert "--convert_model_dtype" in cmd and "--t5_cpu" in cmd
    m, c = _wan_req(tmp_path, extra={"size": "1920*1080"})
    with pytest.raises(PipelineError, match="--size"):
        m.build_command(c, tmp_path / "r.png", tmp_path / "o.mp4")
    m, d = _wan_req(tmp_path, extra={"infer_frames": 48, "num_clip": 2})
    cmd = m.build_command(d, tmp_path / "r.png", tmp_path / "o.mp4")
    assert cmd[cmd.index("--infer_frames") + 1] == "48" and cmd[cmd.index("--num_clip") + 1] == "2"


def test_wan_s2v_sizes_are_the_official_buckets():
    from lipsync_pipeline.models import wan_s2v as w
    assert w.DEFAULT_SIZE in w.SIZES and w.SAMPLE_FPS == 16
    assert max(int(a) * int(b) for a, b in (s.split("*") for s in w.SIZES)) == 1280 * 720 == int(w.DEFAULT_SIZE.split("*")[0]) * int(w.DEFAULT_SIZE.split("*")[1])


def test_wan_s2v_generate_with_fake_tool(tmp_path, monkeypatch):
    import subprocess
    from lipsync_pipeline.utils import video_stream_info
    repo = tmp_path / "Wan2.2"; (repo / "Wan2.2-S2V-14B").mkdir(parents=True)
    (repo / "generate.py").write_text(
        "import argparse, os, subprocess\n"
        "p = argparse.ArgumentParser()\n"
        "for k in ('--image', '--audio', '--save_file', '--prompt'): p.add_argument(k)\n"
        "a, _ = p.parse_known_args()\n"
        "assert os.path.isfile(a.image) and os.path.isfile(a.audio) and a.save_file.endswith('.mp4') and 'cat' not in a.prompt\n"
        "subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=size=960x960:rate=16:duration=1', '-pix_fmt', 'yuv420p', a.save_file], check=True)\n")
    monkeypatch.setenv("WAN22_DIR", str(repo))
    src = tmp_path / "input.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=512x512:rate=24:duration=1", "-pix_fmt", "yuv420p", str(src)], check=True)
    (tmp_path / "audio.wav").write_bytes(b"RIFF")
    m = get_lipsync_model("wan_s2v")
    req = LipSyncRequest(src, tmp_path / "audio.wav", tmp_path / "out.mp4", 24.0, m.resolve(GenerationOptions()))
    m.check_environment(req.options)
    m.generate(req)
    v = video_stream_info(tmp_path / "out.mp4")
    assert (v["width"], v["height"]) == (512, 512)
    monkeypatch.delenv("WAN22_DIR")
    with pytest.raises(PipelineError, match="WAN22_DIR"):
        m.check_environment(req.options)


# ------------------------------------------------------------ 후처리 어댑터 (CodeFormer / Real-ESRGAN / RIFE)
def _make_video(path, size="64x64", rate=24, dur=1.0):
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=size={size}:rate={rate}:duration={dur}",
                    "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


def test_codeformer_command_and_folder_name_rule(tmp_path):
    from lipsync_pipeline.models import get_post_processor
    cf = get_post_processor("restore", "codeformer")
    cmd = cf.build_command(tmp_path / "frames", tmp_path / "out", 0.7)
    assert cmd[1] == "inference_codeformer.py" and "--has_aligned" in cmd
    assert cmd[cmd.index("-w") + 1] == "0.7" and cmd[cmd.index("--input_path") + 1] == str(tmp_path / "frames")
    assert cf.restored_dir(tmp_path / "out") == tmp_path / "out" / "restored_faces"
    with pytest.raises(PipelineError, match="확장자"):            # 폴더 이름이 .png 로 끝나면 CodeFormer 가 단일 이미지로 오인
        cf.build_command(tmp_path / "frames.png", tmp_path / "out", 0.7)


def test_codeformer_process_with_fake_tool(tmp_path, monkeypatch):
    from lipsync_pipeline.models import get_post_processor
    from lipsync_pipeline.utils import video_stream_info
    repo = tmp_path / "CodeFormer"; repo.mkdir()
    (repo / "inference_codeformer.py").write_text(
        "import argparse, glob, os, cv2\n"
        "p = argparse.ArgumentParser(); p.add_argument('-w', type=float); p.add_argument('--has_aligned', action='store_true')\n"
        "p.add_argument('--input_path'); p.add_argument('--output_path'); a = p.parse_args()\n"
        "assert a.has_aligned and os.path.isdir(a.input_path)\n"
        "os.makedirs(os.path.join(a.output_path, 'restored_faces'))\n"
        "for f in sorted(glob.glob(os.path.join(a.input_path, '*.png'))):\n"
        "    img = cv2.resize(cv2.imread(f), (512, 512))\n"                        # has_aligned 는 항상 512x512 로 복원
        "    cv2.imwrite(os.path.join(a.output_path, 'restored_faces', os.path.basename(f)), img)\n")
    monkeypatch.setenv("CODEFORMER_DIR", str(repo))
    src = _make_video(tmp_path / "in.mp4")
    out = get_post_processor("restore", "codeformer").process(src, tmp_path / "restored.mp4", {"weight": 0.5})
    v = video_stream_info(out)
    assert (v["width"], v["height"], v["frames"]) == (512, 512, 24)


def test_realesrgan_video_command_output_rule_and_fp32(tmp_path):
    from lipsync_pipeline.models import get_post_processor
    re_ = get_post_processor("upscale", "realesrgan")
    cmd = re_.build_command(tmp_path / "in.mp4", tmp_path / "out", 2, "RealESRGAN_x4plus", True)
    get = lambda k: cmd[cmd.index(k) + 1]
    assert cmd[1] == "inference_realesrgan_video.py" and get("-n") == "RealESRGAN_x4plus"           # 기본 모델(anime)에 의존하지 않음
    assert get("--outscale") == "2" and get("--suffix") == "out" and "--fp32" in cmd and "--tile" not in cmd
    assert "--fp32" not in re_.build_command(tmp_path / "i.mp4", tmp_path / "o", 2, "m", False)
    assert "--tile" in re_.build_command(tmp_path / "i.mp4", tmp_path / "o", 2, "m", True, tile=400)
    assert re_.expected_video(tmp_path / "out", Path("/x/input.mp4")) == tmp_path / "out" / "input_out.mp4"


def test_realesrgan_frame_fallback_command_forces_fp32(tmp_path):
    from lipsync_pipeline.models import get_post_processor
    cmd = get_post_processor("upscale", "realesrgan").build_frames_command(tmp_path / "f", tmp_path / "o", 2, "RealESRGAN_x4plus")
    assert cmd[1] == "inference_realesrgan.py" and "--fp32" in cmd and cmd[cmd.index("--suffix") + 1] == "" and cmd[cmd.index("--ext") + 1] == "png"


def _fake_realesrgan_repo(repo):
    repo.mkdir()
    (repo / "inference_realesrgan_video.py").write_text(
        "import argparse, os, subprocess\n"
        "p = argparse.ArgumentParser(); p.add_argument('-i'); p.add_argument('-o'); p.add_argument('--suffix', default='out')\n"
        "p.add_argument('-s', '--outscale', type=float); a, _ = p.parse_known_args()\n"
        "os.makedirs(a.o, exist_ok=True); stem = os.path.splitext(os.path.basename(a.i))[0]\n"
        "subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.i, '-vf', f'scale=iw*{a.outscale}:ih*{a.outscale}', '-pix_fmt', 'yuv420p', os.path.join(a.o, f'{stem}_{a.suffix}.mp4')], check=True)\n")
    (repo / "inference_realesrgan.py").write_text(
        "import argparse, glob, os, cv2\n"
        "p = argparse.ArgumentParser(); p.add_argument('-i'); p.add_argument('-o'); p.add_argument('--suffix', default='out')\n"
        "p.add_argument('-s', '--outscale', type=float); a, _ = p.parse_known_args()\n"
        "os.makedirs(a.o, exist_ok=True)\n"
        "for f in sorted(glob.glob(os.path.join(a.i, '*.png'))):\n"
        "    img = cv2.imread(f); img = cv2.resize(img, None, fx=a.outscale, fy=a.outscale)\n"
        "    name = os.path.splitext(os.path.basename(f))[0]; cv2.imwrite(os.path.join(a.o, f'{name}_{a.suffix}.png' if a.suffix else f'{name}.png'), img)\n")


@pytest.mark.parametrize("gpus", [1, 0])
def test_realesrgan_process_video_script_or_cpu_frame_fallback(tmp_path, monkeypatch, gpus):
    from lipsync_pipeline.models import get_post_processor
    from lipsync_pipeline.utils import video_stream_info
    repo = tmp_path / "Real-ESRGAN"; _fake_realesrgan_repo(repo)
    monkeypatch.setenv("REALESRGAN_DIR", str(repo))
    src = _make_video(tmp_path / "내 입력 영상.mp4", dur=0.5)                 # 한글/공백 경로
    out = get_post_processor("upscale", "realesrgan").process(src, tmp_path / "up.mp4", {"scale": 2, "cuda_devices": gpus})
    v = video_stream_info(out)
    assert (v["width"], v["height"], v["frames"]) == (128, 128, 12) and abs(v["fps"] - 24) < 0.01


def test_realesrgan_cuda_probe_failure_means_unknown(monkeypatch):
    from lipsync_pipeline.models import realesrgan as r
    monkeypatch.setenv("LIPSYNC_TOOL_PYTHON", "/nonexistent/python")
    assert r.cuda_device_count() == -1


def test_rife_command_uses_png_mode_and_absolute_model(tmp_path):
    from lipsync_pipeline.models import get_post_processor
    rf = get_post_processor("interpolate", "rife")
    cmd = rf.build_command(tmp_path / "RIFE", tmp_path / "in.mp4", 2)
    assert cmd[1] == str(tmp_path / "RIFE" / "inference_video.py") and "--multi=2" in cmd and "--png" in cmd
    assert f"--model={tmp_path / 'RIFE' / 'train_log'}" in cmd and "--fp16" not in cmd and "--output" not in " ".join(cmd)   # mp4v 출력 안 씀
    assert "--fp16" in rf.build_command(tmp_path / "RIFE", tmp_path / "in.mp4", 2, fp16=True)
    with pytest.raises(PipelineError, match="scale"):
        rf.build_command(tmp_path / "RIFE", tmp_path / "in.mp4", 2, scale=0.7)       # 허용: 0.25/0.5/1/2/4
    with pytest.raises(PipelineError, match="2 이상"):
        rf.build_command(tmp_path / "RIFE", tmp_path / "in.mp4", 1)
    assert rf.output_fps("24/1", 2) == "48/1" and rf.output_fps("30000/1001", 2) == "60000/1001"
    assert rf.expected_frames(24, 2) == 47            # (n-1)*multi + 1


def test_rife_process_with_fake_tool(tmp_path, monkeypatch):
    from lipsync_pipeline.models import get_post_processor
    from lipsync_pipeline.utils import video_stream_info
    repo = tmp_path / "Practical-RIFE"; (repo / "train_log").mkdir(parents=True)
    (repo / "inference_video.py").write_text(
        "import argparse, os, subprocess, glob, shutil, tempfile, cv2\n"
        "p = argparse.ArgumentParser(); p.add_argument('--video'); p.add_argument('--multi', type=int); p.add_argument('--png', action='store_true')\n"
        "p.add_argument('--model'); p.add_argument('--scale'); a, _ = p.parse_known_args()\n"
        "assert a.png and os.path.isfile(os.path.join(a.model, 'flownet.pkl'))\n"
        "d = tempfile.mkdtemp(); subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.video, os.path.join(d, '%d.png')], check=True)\n"
        "fr = sorted(glob.glob(os.path.join(d, '*.png')), key=lambda x: int(os.path.basename(x)[:-4])); os.makedirs('vid_out', exist_ok=True)\n"
        "out = []\n"
        "for i in range(len(fr) - 1):\n"
        "    out += [fr[i]] + [fr[i]] * (a.multi - 1)\n"
        "out.append(fr[-1])\n"
        "for k, f in enumerate(out): shutil.copyfile(f, 'vid_out/{:0>7d}.png'.format(k))\n")
    monkeypatch.setenv("RIFE_DIR", str(repo))
    rf = get_post_processor("interpolate", "rife")
    src = _make_video(tmp_path / "in.mp4", dur=0.5)
    with pytest.raises(PipelineError, match="flownet.pkl"):
        rf.process(src, tmp_path / "x.mp4", {"multi": 2})
    (repo / "train_log" / "flownet.pkl").write_text("w")
    out = rf.process(src, tmp_path / "interp.mp4", {"multi": 2})
    v = video_stream_info(out)
    assert abs(v["fps"] - 48) < 0.01 and v["frames"] == 23 and (v["width"], v["height"]) == (64, 64)          # 12 -> (12-1)*2+1


# ------------------------------------------------------------ 도구별 파이썬 선택
def test_tool_python_precedence(monkeypatch):
    import sys
    from lipsync_pipeline.models.base import py
    for k in ("LIPSYNC_TOOL_PYTHON", "LIPSYNC_TOOL_PYTHON_RIFE"):
        monkeypatch.delenv(k, raising=False)
    assert py() == py("rife") == sys.executable
    monkeypatch.setenv("LIPSYNC_TOOL_PYTHON", "/envs/common/bin/python")
    assert py() == py("rife") == "/envs/common/bin/python"
    monkeypatch.setenv("LIPSYNC_TOOL_PYTHON_RIFE", "/envs/rife/bin/python")
    assert py("rife") == "/envs/rife/bin/python" and py("codeformer") == "/envs/common/bin/python" and py() == "/envs/common/bin/python"


def test_every_adapter_command_uses_its_own_tool_python(tmp_path, monkeypatch):
    from lipsync_pipeline.models import get_post_processor
    monkeypatch.setenv("LIPSYNC_TOOL_PYTHON", "/common/python")
    for n in ("MUSETALK", "INFINITETALK", "WAN_S2V", "CODEFORMER", "REALESRGAN", "RIFE"):
        monkeypatch.setenv(f"LIPSYNC_TOOL_PYTHON_{n}", f"/envs/{n.lower()}/python")
    mk = lambda n: (get_lipsync_model(n), None)
    for name, build in (
        ("musetalk", lambda m, r: m.build_command(r, tmp_path / "c.yaml", tmp_path / "r")),
        ("infinitetalk", lambda m, r: m.build_command(r, tmp_path / "i.json", tmp_path / "r", tmp_path / "e")),
        ("wan_s2v", lambda m, r: m.build_command(r, tmp_path / "r.png", tmp_path / "o.mp4")),
    ):
        m = get_lipsync_model(name)
        req = LipSyncRequest(tmp_path / "i.mp4", tmp_path / "a.wav", tmp_path / "o.mp4", 24.0, m.resolve(GenerationOptions()))
        assert build(m, req)[0] == f"/envs/{name}/python"
    assert get_post_processor("restore", "codeformer").build_command(tmp_path / "f", tmp_path / "o", 0.7)[0] == "/envs/codeformer/python"
    assert get_post_processor("upscale", "realesrgan").build_command(tmp_path / "i.mp4", tmp_path / "o", 2, "m", True)[0] == "/envs/realesrgan/python"
    assert get_post_processor("interpolate", "rife").build_command(tmp_path / "R", tmp_path / "i.mp4", 2)[0] == "/envs/rife/python"
    # LatentSync 는 건드리지 않았으므로 기존대로 공통 변수를 쓴다
    ls = get_lipsync_model("latentsync")
    req = LipSyncRequest(tmp_path / "i.mp4", tmp_path / "a.wav", tmp_path / "o.mp4", 24.0, ls.resolve(GenerationOptions()))
    assert ls.build_command(req, tmp_path)[0] == "/common/python"


def test_latentsync_pads_crop_so_face_detector_sees_margin_and_restores_original_size(tmp_path, monkeypatch):
    """얼굴이 화면을 꽉 채우면 LatentSync 검출기가 실패한다(실측). 여백을 붙여 모델에 넘기고 결과는 원래 크기로 되돌린다."""
    import shutil
    import subprocess
    import cv2
    from lipsync_pipeline.models import latentsync as ls
    from lipsync_pipeline.models.base import GenerationOptions, LipSyncRequest
    from lipsync_pipeline.utils import video_stream_info

    src = tmp_path / "내 입력.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=96x96:rate=24", "-frames:v", "12",
                    "-pix_fmt", "yuv420p", str(src)], check=True)
    seen = {}

    def fake_tool(cmd, cwd, what):                         # 모델이 받은 입력의 크기를 기록하고, 그대로 복사해서 결과로 낸다
        cmd = [str(c) for c in cmd]
        vin, vout = cmd[cmd.index("--video_path") + 1], cmd[cmd.index("--video_out_path") + 1]
        seen["size"] = (video_stream_info(Path(vin))["width"], video_stream_info(Path(vin))["height"])
        shutil.copy(vin, vout)

    monkeypatch.setattr(ls, "run_tool", fake_tool)
    m = get_lipsync_model("latentsync")
    opts = m.resolve(GenerationOptions(tool_dir=str(tmp_path)))
    out = tmp_path / "out.mp4"
    req = LipSyncRequest(src, tmp_path / "a.wav", out, 24.0, opts)
    m.generate(req)

    side = ls.padded_canvas_side(96, 96)
    assert seen["size"] == (side, side) and side > 96 and 96 / side <= 0.6 + 0.02       # 모델은 여백 있는 큰 캔버스를 받는다
    info = video_stream_info(out)
    assert (info["width"], info["height"], info["frames"]) == (96, 96, 12)                # 결과는 원래 크기/프레임 수
    assert not list(tmp_path.glob("*.pad_*.mp4"))                                           # 임시 파일 정리

    def first(p):
        ok, f = cv2.VideoCapture(str(p)).read()
        assert ok
        return f.astype("int16")
    assert abs(first(src) - first(out)).mean() < 4                                          # 가운데 영역이 원본과 같다(손실 압축 오차만)
