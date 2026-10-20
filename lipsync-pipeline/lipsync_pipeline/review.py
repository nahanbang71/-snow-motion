"""review: 로컬 웹 UI. 구간별 후보를 나란히 보고 베스트를 고른다 -> selection.json.

표준 라이브러리 http.server 만 사용 (설치 불필요). 127.0.0.1 에만 바인딩하고, 변경 요청에는 실행마다 새로
만드는 토큰을 요구한다. 점수는 참고용이며 선택은 항상 사용자가 한다.
"""
from __future__ import annotations

import json
import mimetypes
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .generate import existing_takes, generate_takes
from .models import GenerationOptions, available_models
from .selection import load_selection, set_selection
from .utils import PipelineError, Workspace, log, read_json

PAGE = r"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>립싱크 후보 선택</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#f6f6f4;--fg:#1d1d1b;--card:#fff;--line:#d9d9d4;--acc:#1f6feb;--ok:#1a7f37}
@media(prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ececea;--card:#222220;--line:#3a3a36;--acc:#58a6ff;--ok:#3fb950}}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,"Malgun Gothic",sans-serif}
header{position:sticky;top:0;background:var(--card);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
main{padding:16px;display:grid;gap:16px}
.seg{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}
.seg h2{margin:0 0 8px;font-size:15px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.row{display:flex;gap:12px;overflow-x:auto;padding-bottom:6px}
.take{flex:0 0 260px;border:2px solid var(--line);border-radius:8px;padding:6px}
.take.sel{border-color:var(--ok)}
video{width:100%;border-radius:6px;background:#000}
.meta{font-size:12px;opacity:.85;min-height:3.6em}
button,select,input{font:inherit}
button{cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:6px;padding:4px 10px}
button.primary{background:var(--acc);border-color:var(--acc);color:#fff}
.note{font-size:12px;opacity:.75}
#status{font-size:12px}
</style></head><body>
<header><strong id="title"></strong><span id="progress"></span><span id="status"></span>
<span class="note">자동 점수는 참고용입니다. 최종 선택은 직접 하세요.</span></header>
<main id="main"></main>
<script>
const TOKEN="__TOKEN__";
const $=(t,a={},...c)=>{const e=document.createElement(t);for(const[k,v]of Object.entries(a)){if(k==="class")e.className=v;else if(k.startsWith("on"))e.addEventListener(k.slice(2),v);else e.setAttribute(k,v)}for(const x of c)e.append(x);return e};
const api=(p,body)=>fetch(p,body?{method:"POST",headers:{"Content-Type":"application/json","X-Token":TOKEN},body:JSON.stringify(body)}:{}).then(r=>r.json());
function fmtScores(s){if(!s)return"점수 없음";const p=[];
 if(s.sync_proxy)p.push(`싱크(간이) ${s.sync_proxy.corr} (지연 ${s.sync_proxy.lag_frames}f)`);
 if(s.syncnet)p.push(`SyncNet ${JSON.stringify(s.syncnet)}`);
 if(s.stable_pct!==undefined)p.push(`안정도 ${s.stable_pct}% (윗얼굴 떨림 ${s.flicker_upper}, 입 가속도 ${s.mouth_accel})`);
 return p.join(" · ")}
async function load(){const st=await api("/api/state");document.getElementById("title").textContent=st.name;
 const main=document.getElementById("main");main.replaceChildren();
 let done=0;
 for(const sg of st.segments){const sel=st.selection[String(sg.index)];if(sel)done++;
  const row=$("div",{class:"row"});const vids=[];
  const add=(label,src,meta,takeNo)=>{const v=$("video",{src,controls:"",muted:"",loop:"",preload:"metadata"});v.muted=true;vids.push(v);
   const box=$("div",{class:"take"+(takeNo&&takeNo===sel?" sel":"")},$("div",{},label),v,$("div",{class:"meta"},meta||""));
   if(takeNo){const r=$("input",{type:"radio",name:"s"+sg.index});r.checked=(takeNo===sel);
    r.addEventListener("change",async()=>{await api("/api/select",{segment:sg.index,take:takeNo});load()});
    box.append($("label",{},r," 이 후보를 사용"))}
   row.append(box)};
  add("원본 입력",`/file/${sg.dir}/input.mp4`,`프레임 ${sg.range[0]}~${sg.range[1]}`);
  for(const t of sg.takes)add(`take_${t.take} · ${t.model}${t.label?" · "+t.label:""}`,`/file/${sg.dir}/take_${t.take}.mp4`,`seed ${t.seed} · ${fmtScores(t.scores)}`,t.take);
  const audio=$("audio",{src:`/file/${sg.dir}/audio.wav`});
  const play=$("button",{class:"primary",onclick:()=>{vids.forEach(v=>{v.currentTime=0;v.play()});audio.currentTime=0;audio.play()}},"▶ 동시 재생(오디오 포함)");
  const stop=$("button",{onclick:()=>{vids.forEach(v=>v.pause());audio.pause()}},"■ 정지");
  const n=$("input",{type:"number",min:1,max:20,value:3,style:"width:3.5em"});
  const m=$("select",{});for(const x of st.models)m.append($("option",{value:x},x));m.value=st.default_model;
  const seed=$("input",{type:"number",placeholder:"seed(선택)",style:"width:7em"});
  const regen=$("button",{onclick:async()=>{const r=await api("/api/regenerate",{segment:sg.index,takes:+n.value,model:m.value,seed:seed.value?+seed.value:null});
    document.getElementById("status").textContent=r.error?("오류: "+r.error):"재생성 시작...";poll()}},"이 구간 재생성");
  main.append($("section",{class:"seg"},$("h2",{},`구간 ${sg.index}`,$("span",{class:"note"},`${(sg.range[0]/st.fps).toFixed(2)}~${(sg.range[1]/st.fps).toFixed(2)}초`),play,stop,
    $("span",{class:"note"},"재생성:"),n,"개",m,seed,regen),row,audio))}
 document.getElementById("progress").textContent=`선택 ${done}/${st.segments.length}`}
let timer=null;
function poll(){if(timer)return;timer=setInterval(async()=>{const s=await api("/api/status");
 document.getElementById("status").textContent=s.running?("생성 중: "+s.message):(s.error?("오류: "+s.error):(s.message||""));
 if(!s.running){clearInterval(timer);timer=null;load()}},2000)}
load();poll();
</script></body></html>"""


class ReviewState:
    def __init__(self, ws: Workspace, default_model: str, options: GenerationOptions):
        self.ws, self.default_model, self.options = ws, default_model, options
        self.token = secrets.token_urlsafe(16)
        self.lock = threading.Lock()
        self.job = {"running": False, "message": "", "error": ""}

    def state(self) -> dict:
        plan = read_json(self.ws.p("segments.json"))
        segs = []
        for sg in plan["segments"]:
            d = self.ws.p(sg["dir"])
            takes = []
            for t in existing_takes(d):
                mp = d / f"take_{t}.json"
                meta = read_json(mp) if mp.exists() else {}
                takes.append({"take": t, "model": meta.get("model", "?"), "label": meta.get("label", ""),
                              "seed": meta.get("seed"), "scores": meta.get("scores")})
            segs.append({**sg, "takes": takes})
        return {"name": self.ws.name, "fps": plan["fps"], "segments": segs,
                "selection": load_selection(self.ws)["segments"], "models": available_models()["lipsync"],
                "default_model": self.default_model}

    def start_regenerate(self, segment: int, takes: int, model: str, seed) -> None:
        with self.lock:
            if self.job["running"]:
                raise PipelineError("이미 다른 재생성이 진행 중입니다.")
            self.job = {"running": True, "message": f"구간 {segment} ({model}) 후보 {takes}개", "error": ""}
        opts = GenerationOptions(**{**self.options.to_dict(), **({"seed": seed} if seed is not None else {})})

        def work():
            try:
                generate_takes(self.ws, model, takes, opts, only=[segment], label="regen")
                msg, err = f"구간 {segment} 재생성 완료", ""
            except Exception as e:          # UI 에 그대로 보여준다
                msg, err = "", str(e)
            with self.lock:
                self.job = {"running": False, "message": msg, "error": err}
        threading.Thread(target=work, daemon=True).start()


def make_handler(st: ReviewState):
    root = st.ws.root.resolve()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                b = PAGE.replace("__TOKEN__", st.token).encode("utf-8")
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            elif path == "/api/state":
                self._json(st.state())
            elif path == "/api/status":
                with st.lock:
                    self._json(dict(st.job))
            elif path.startswith("/file/"):
                self._file(unquote(path[len("/file/"):]))
            else:
                self.send_error(404)

        def _file(self, rel):
            p = (root / rel).resolve()
            if root not in p.parents or not p.is_file() or not re.match(r"^segments/", p.relative_to(root).as_posix()):
                return self.send_error(404)
            size = p.stat().st_size
            start, end = 0, size - 1
            m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
            code = 200
            if m and (m.group(1) or m.group(2)):
                if m.group(1):
                    start = int(m.group(1)); end = int(m.group(2)) if m.group(2) else end
                else:
                    start = max(size - int(m.group(2)), 0)
                end = min(end, size - 1)
                if start > end:
                    return self.send_error(416)
                code = 206
            self.send_response(code)
            self.send_header("Content-Type", mimetypes.guess_type(p.name)[0] or "application/octet-stream")
            self.send_header("Accept-Ranges", "bytes"); self.send_header("Content-Length", str(end - start + 1))
            if code == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            with open(p, "rb") as f:
                f.seek(start); left = end - start + 1
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    left -= len(chunk)

        def do_POST(self):
            if self.headers.get("X-Token") != st.token:
                return self._json({"error": "토큰이 올바르지 않습니다."}, 403)
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                path = urlparse(self.path).path
                if path == "/api/select":
                    set_selection(st.ws, int(body["segment"]), int(body["take"]))
                    return self._json({"ok": True})
                if path == "/api/regenerate":
                    st.start_regenerate(int(body["segment"]), max(1, min(int(body.get("takes", 3)), 20)),
                                        body.get("model") or st.default_model, body.get("seed"))
                    return self._json({"ok": True})
                self._json({"error": "알 수 없는 요청"}, 404)
            except (PipelineError, KeyError, ValueError) as e:
                self._json({"error": str(e)}, 400)

    return H


def serve(ws: Workspace, port: int = 8765, default_model: str = "latentsync",
          options: GenerationOptions | None = None, open_browser: bool = True) -> None:
    st = ReviewState(ws, default_model, options or GenerationOptions())
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(st))
    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    log(f"[review] {url}  (Ctrl+C 로 종료) — 선택은 {ws.p('selection.json')} 에 저장됩니다.")
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
