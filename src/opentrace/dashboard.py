"""Read-only dashboard served on loopback."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from .db import connect
from .cli import _session_records


def serve(host="127.0.0.1", port=8765):
    db = connect()
    try:
        records = _session_records(db)
    finally:
        db.close()
    data = json.dumps(records).replace("<", "\\u003c")
    page = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>OpenTrace</title><style>
body{font:15px system-ui;background:#111827;color:#f9fafb;max-width:1000px;margin:36px auto;padding:0 20px}
small{color:#9ca3af}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
article{background:#1f2937;border:1px solid #374151;border-radius:12px;padding:16px;margin:16px 0}
.metric{font-size:26px;font-weight:700}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #374151}
</style></head><body><h1>OpenTrace</h1><small>Local session dashboard · no cloud connection</small>
<div class="grid"><article>Sessions<div class="metric" id="sessions"></div></article>
<article>Input tokens<div class="metric" id="input"></div></article>
<article>Output tokens<div class="metric" id="output"></div></article>
<article>Estimated cost<div class="metric" id="cost"></div></article></div>
<article><h2>Sessions</h2><table><thead><tr><th>Task</th><th>Status</th><th>Tokens</th><th>Est. cost</th></tr></thead><tbody id="rows"></tbody></table></article>
<script>const data=__DATA__;const fmt=n=>Number(n||0).toLocaleString();const total=k=>data.reduce((a,s)=>a+s.usage.reduce((b,u)=>b+Number(u[k]||0),0),0);
document.getElementById('sessions').textContent=fmt(data.length);document.getElementById('input').textContent=fmt(total('input_tokens'));document.getElementById('output').textContent=fmt(total('output_tokens'));
document.getElementById('cost').textContent='$'+data.reduce((a,s)=>a+Number(s.estimated_cost_usd||0),0).toFixed(4);
document.getElementById('rows').innerHTML=data.map(s=>'<tr><td>'+esc(s.task)+'</td><td>'+esc(s.status)+'</td><td>'+fmt(s.usage.reduce((a,u)=>a+u.input_tokens+u.output_tokens,0))+'</td><td>$'+Number(s.estimated_cost_usd||0).toFixed(4)+'</td></tr>').join('')||'<tr><td colspan="4">No sessions recorded</td></tr>';
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}</script></body></html>""".replace("__DATA__", data)
    payload = page.encode("utf-8")
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, *_args):
            return
    print(f"Dashboard: http://{host}:{port} (Ctrl+C to stop)")
    HTTPServer((host, port), Handler).serve_forever()
