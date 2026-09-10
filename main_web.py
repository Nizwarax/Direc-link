from flask import Flask, jsonify, render_template, request, send_file
import json, os, subprocess, sys, tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

def run_engine(url):
    proc = subprocess.run(
        [sys.executable, os.path.join(BASE, "main.py"), url, "--direct"],
        cwd=BASE, capture_output=True, text=True, timeout=65
    )
    stdout=(proc.stdout or "").strip()
    stderr=(proc.stderr or "").strip()
    try:
        data=json.loads(stdout) if stdout else {}
    except:
        data={}
    if proc.returncode != 0:
        return None, stderr or stdout or "engine gagal"
    return data, None

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/api/generate")
def generate():
    p=request.get_json(silent=True) or {}
    url=str(p.get("url") or "").strip()
    if not url:
        return jsonify(ok=False,error="Masukkan URL Sfile"),400
    data,e=run_engine(url)
    if e: return jsonify(ok=False,error=e),502
    best=data.get("cdn_url") or data.get("direct_url")
    return jsonify(ok=True, title=data.get("title"), size=data.get("size"),
                   best_url=best, direct_url=data.get("direct_url"),
                   cdn_url=data.get("cdn_url"), data=data)

@app.get("/api/download")
def download():
    url=str(request.args.get("url") or "").strip()
    if not url:
        return jsonify(ok=False,error="url kosong"),400
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".bin")
    tmp.close()
    try:
        proc=subprocess.run(
            [ "node", os.path.join(BASE,"downloader.js"), "download", url, tmp.name ],
            cwd=BASE, capture_output=True, text=True, timeout=180
        )
        if proc.returncode != 0:
            return jsonify(ok=False,error=proc.stderr or proc.stdout),502
        info={}
        try: info=json.loads(proc.stdout.strip().splitlines()[-1])
        except: pass
        if not os.path.exists(tmp.name) or os.path.getsize(tmp.name)==0:
            return jsonify(ok=False,error="file kosong", debug={"stdout":proc.stdout, "stderr":proc.stderr}),502
        return send_file(tmp.name, as_attachment=True,
                         download_name=info.get("download",{}).get("filename","sfile_download"))
    except Exception as e:
        return jsonify(ok=False,error=str(e)),502

@app.get("/health")
def health():
    return jsonify(ok=True)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
