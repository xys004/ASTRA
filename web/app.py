import os
import threading
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.state import state
from main import start_background_loop

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace", "uploads")
ASSETS_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace", "assets")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace", "reports")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR,  exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Start background ASTRA loop — errors are caught and logged rather than crashing the thread
def _safe_background_loop():
    try:
        start_background_loop()
    except Exception as exc:
        state.add_log(f"[FATAL] Background loop terminated unexpectedly: {exc}")
        state.status = "IDLE"

threading.Thread(target=_safe_background_loop, daemon=True).start()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/api/state')
def get_state():
    return jsonify(state.get_state_dict())


@app.route('/api/start', methods=['POST'])
def start_loop():
    data = request.json or {}
    intuition = data.get('intuition', '')
    if intuition:
        state.current_intuition = intuition

    providers = data.get('providers', {})
    if providers:
        if 'conjecture' in providers:
            os.environ['ASTRA_CONJECTURE_PROVIDER'] = providers['conjecture']
        if 'translator' in providers:
            os.environ['ASTRA_TRANSLATOR_PROVIDER'] = providers['translator']
        if 'analyst' in providers:
            os.environ['ASTRA_ANALYST_PROVIDER'] = providers['analyst']

    state.start_loop_requested = True
    return jsonify({"success": True})


@app.route('/api/stop', methods=['POST'])
def stop_loop():
    state.stop_requested = True
    state.add_log("Stop requested by user.")
    return jsonify({"success": True})


@app.route('/api/approve', methods=['POST'])
def approve():
    state.approve_theorem_requested = True
    return jsonify({"success": True})


@app.route('/api/reject', methods=['POST'])
def reject():
    state.reject_theorem_requested = True
    return jsonify({"success": True})


@app.route('/api/reports')
def reports():
    return jsonify({"reports": state.reports})


@app.route('/reports/<path:filename>')
def report_file(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=False)


@app.route('/api/upload_doc', methods=['POST'])
def upload_doc():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOADS_DIR, filename)
    file.save(filepath)

    extracted_text = f"Attached document: {filename}\n\n"

    if filename.lower().endswith('.pdf'):
        try:
            import fitz  # lazy import — optional dependency
            with fitz.open(filepath) as doc:
                for page in doc:
                    extracted_text += page.get_text() + "\n"
        except ImportError:
            return jsonify({"error": "PyMuPDF not installed. Run: pip install PyMuPDF"}), 500
        except Exception as exc:
            return jsonify({"error": f"Failed to parse PDF: {exc}"}), 500
    else:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                extracted_text += f.read()
        except UnicodeDecodeError:
            return jsonify({"error": "File encoding not supported. Use UTF-8 text files."}), 400

    state.current_intuition = extracted_text
    state.add_log(f"Document '{filename}' uploaded and parsed successfully.")
    return jsonify({"success": True, "message": "Document loaded into ASTRA context."})


@app.route('/api/upload_asset', methods=['POST'])
def upload_asset():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(ASSETS_DIR, filename)
    file.save(filepath)
    return jsonify({"success": True, "message": f"Asset '{filename}' saved."})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5050, debug=False)
