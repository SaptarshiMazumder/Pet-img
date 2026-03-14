"""Flask app — HTTP routes only. All logic lives in scaling.py and jobs.py."""
import threading

from flask import Flask, jsonify, request
from flask_cors import CORS

import autoscaler.jobs as jobs
import autoscaler.scaling as scaling

app = Flask(__name__)
CORS(app)


# -- Scaling routes ----------------------------------------------------------

@app.route("/warm", methods=["POST"])
def route_warm():
    threading.Thread(target=scaling.warm, daemon=True).start()
    return jsonify({"ok": True})


@app.route("/job/start", methods=["POST"])
def route_job_start():
    scaling.on_job_start()
    return jsonify({"ok": True})


@app.route("/job/finish", methods=["POST"])
def route_job_finish():
    scaling.on_job_finish()
    return jsonify({"ok": True})


@app.route("/status", methods=["GET"])
def route_status():
    import time
    from autoscaler.scaling import _lock, _active_count, _queue_empty_since, _has_had_activity
    with _lock:
        count = _active_count
        empty_since = _queue_empty_since
        activity = _has_had_activity
    idle = int(time.time() - empty_since) if empty_since else 0
    return jsonify({
        "active_jobs": count,
        "idle_seconds": idle,
        "has_had_activity": activity,
    })


# -- Job store routes --------------------------------------------------------

@app.route("/job", methods=["POST"])
def route_create_job():
    data = request.get_json(silent=True) or {}
    job_id = data.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id required"}), 400
    jobs.create(job_id)
    return jsonify({"ok": True}), 201


@app.route("/job/<job_id>", methods=["GET"])
def route_get_job(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/job/<job_id>", methods=["PATCH"])
def route_update_job(job_id: str):
    data = request.get_json(silent=True) or {}
    if not jobs.update(job_id, data):
        return jsonify({"error": "Job not found"}), 404
    return jsonify({"ok": True})
