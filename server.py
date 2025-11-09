from gevent.pywsgi import WSGIServer
from flask import Flask, request, send_file
from threading import Thread
import subprocess, os, sys, schedule, time
from gevent import monkey
monkey.patch_all()

# --- CONFIGURATION ---
VERSION = "1.0"
PROVIDER_NAME = "Xumo"

GENERATOR_INTERVAL_HOURS = 12

EPG_FILENAME_XML = "xumo_epg.xml"
PLAYLIST_FILENAME = "xumo_playlist.m3u"

# Must match generate_xumo.py default; allow override via env
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/data/playlists")
GENERATOR_SCRIPT = "./generate_xumo.py"

# Ensure the output dir exists right away so the index can render
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Port from env
try:
    port = int(os.environ.get("XUMO_PORT", 7779))
except Exception:
    port = 7779

app = Flask(__name__)

@app.route("/health")
def health():
    return "OK", 200

@app.route("/")
def index():
    host = request.host
    playlist_path = os.path.join(OUTPUT_DIR, PLAYLIST_FILENAME)
    files_exist = os.path.exists(playlist_path)

    pl_url = f"http://{host}{'' if OUTPUT_DIR.startswith('/') else '/'}{OUTPUT_DIR}/{PLAYLIST_FILENAME}"
    epg_xml_url = f"http://{host}{'' if OUTPUT_DIR.startswith('/') else '/'}{OUTPUT_DIR}/{EPG_FILENAME_XML}"

    if files_exist:
        try:
            file_mtime = os.path.getmtime(playlist_path)
            file_age_minutes = (time.time() - file_mtime) / 60
            file_status_message = f"Files generated {file_age_minutes:.1f} minutes ago."
            content_list_html = f"""
                <ul class="file-list">
                    <li>
                        <strong>Playlist URL (M3U)</strong>
                        <a href="{pl_url}">{pl_url}</a>
                    </li>
                    <li>
                        <strong>EPG URL (XMLTV)</strong>
                        <a href="{epg_xml_url}">{epg_xml_url}</a>
                    </li>
                </ul>
            """
        except Exception:
            file_status_message = "Files found, but age calculation failed."
            content_list_html = ""
    else:
        file_status_message = "Status: Generator has not completed its first run. Links will appear here when files are ready."
        content_list_html = ""

    html = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Xumo For Channels</title>
    <style>
      body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #f7f9fc; color: #1f2937;
        display: flex; justify-content: center; align-items: center;
        min-height: 100vh; margin: 0;
      }}
      .container {{
        background: #ffffff; padding: 30px 40px; border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        max-width: 600px; width: 90%; text-align: center;
      }}
      h1 {{ color: #4c51bf; font-size: 1.8rem; margin-bottom: 5px; }}
      p {{ color: #6b7280; margin-bottom: 25px; }}
      .file-list {{ list-style: none; padding: 0; text-align: left; }}
      .file-list li {{
        margin-bottom: 20px; padding: 15px; border: 1px solid #e5e7eb;
        border-radius: 8px; background-color: #f9fafb; transition: border-color 0.2s;
      }}
      .file-list li:hover {{ border-color: #4c51bf; }}
      .file-list strong {{
        display: block; font-size: 1.1rem; color: #1f2937; margin-bottom: 8px;
      }}
      .file-list a {{
        display: block; padding: 10px; background-color: #f3f4f6; color: #4c51bf;
        text-decoration: none; border-radius: 6px; font-family: 'Courier New', monospace;
        font-size: 0.9em; word-break: break-all; transition: background-color 0.2s;
      }}
      .file-list a:hover {{ background-color: #e5e7eb; }}
      .status {{ margin-top: 30px; font-size: 0.85em; color: #9ca3af; }}
    </style>
  </head>
  <body>
    <div class="container">
      <h1>📺 Xumo For Channels (v{VERSION})</h1>
      <p>Server running on port {port}.</p>
      {content_list_html}
      <div class="status">
        <p>{file_status_message}</p>
        <p>Files update interval is set to {GENERATOR_INTERVAL_HOURS} hours.</p>
      </div>
    </div>
  </body>
</html>
"""
    return html

# Serve generated files; handle absolute OUTPUT_DIR (e.g. /data/playlists)
route_prefix = OUTPUT_DIR if OUTPUT_DIR.startswith('/') else f"/{OUTPUT_DIR}"

@app.route(f"{route_prefix}/<path:filename>")
def serve_file(filename):
    file_path = os.path.join(OUTPUT_DIR, filename)
    try:
        if filename == PLAYLIST_FILENAME:
            return send_file(file_path, as_attachment=False, mimetype='audio/x-mpegurl')
        elif filename == EPG_FILENAME_XML:
            return send_file(file_path, as_attachment=False, mimetype='text/xml')
        else:
            return "File not found or unauthorized", 404
    except FileNotFoundError:
        return f"{filename} not found. Check if the generator script ran successfully.", 404
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

# --- SCHEDULING LOGIC ---
def run_generator_script():
    print(f"\n--- [Scheduler] Running {GENERATOR_SCRIPT} at {time.ctime()} ---")
    try:
        # Stream stdout/stderr live to container logs
        subprocess.run([sys.executable, GENERATOR_SCRIPT], check=True)
        print(f"--- [Scheduler] Finished at {time.ctime()} ---")
    except subprocess.CalledProcessError as e:
        print(f"!!! [Scheduler] ERROR: Script failed with return code {e.returncode}")
    except FileNotFoundError:
        print(f"!!! [Scheduler] ERROR: Generator script {GENERATOR_SCRIPT} not found.")

def scheduler_thread():
    schedule.every(GENERATOR_INTERVAL_HOURS).hours.do(run_generator_script)

    playlist_path = os.path.join(OUTPUT_DIR, PLAYLIST_FILENAME)
    files_exist = os.path.exists(playlist_path)

    if files_exist:
        try:
            file_mtime = os.path.getmtime(playlist_path)
            file_age_hours = (time.time() - file_mtime) / 3600
            if file_age_hours >= GENERATOR_INTERVAL_HOURS:
                print(f"--- [Scheduler Init] Files are {file_age_hours:.1f} hours old (stale). Running generator immediately... ---")
                run_generator_script()
            else:
                hours_remaining = max(0.0, GENERATOR_INTERVAL_HOURS - file_age_hours)
                print(f"--- [Scheduler Init] Files are fresh ({file_age_hours:.1f} hours old). Next run scheduled in {hours_remaining:.1f} hours. ---")
        except Exception as e:
            print(f"!!! [Scheduler Init] ERROR during file time check: {e}. Running generator as safeguard.")
            run_generator_script()
    else:
        print("\n--- [Scheduler Init] Output files not found. Running initial generator script... ---")
        run_generator_script()

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"Scheduler crashed: {e}. Restarting...")
            time.sleep(5)

if __name__ == '__main__':
    sys.stdout.write(f"> HTTP server started on [::]:{port}. Initial file check running in background.\n")
    try:
        thread = Thread(target=scheduler_thread, daemon=True)
        thread.start()
        WSGIServer(('0.0.0.0', port), app, log=None).serve_forever()
    except OSError as e:
        print(f"!!! SERVER STARTUP ERROR: {str(e)}")
        print("Ensure port is available and server is bound correctly.")
