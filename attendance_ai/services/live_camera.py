import time
import cv2
import numpy as np
from typing import Dict, Any, Optional
from attendance_ai.services.face_recognition import FaceRecognitionService

# TUNE THESE
CONFIDENCE_THRESHOLD = 0.72   # cosine-based mapped [0..1]. increase to be stricter
L2_THRESHOLD = 0.9            # L2 distance threshold (lower = stricter)
MIN_SECONDS_BETWEEN_PUNCHES = 60  # per-user cooldown to avoid duplicate punches

class LiveAttendanceEngine:
    def __init__(self, known_embeddings: Dict[int, np.ndarray], user_meta: Dict[int, Dict[str, Any]]):
        """
        known_embeddings: {user_id: embedding_np}
        user_meta: optional metadata {user_id: {"username": "...", ...}}
        """
        self.known_embeddings = known_embeddings
        self.user_meta = user_meta
        self.last_punch_ts: Dict[int, float] = {}  # user_id -> last punch timestamp

    def match_embedding(self, emb: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Compare live emb to stored embeddings. Return best-match dict or None.
        Result example: {"user_id": id, "dist": 0.65, "conf": 0.85}
        """
        best = None
        for uid, known in self.known_embeddings.items():
            dist = FaceRecognitionService.l2_distance(known, emb)
            conf = FaceRecognitionService.calculate_confidence(known, emb)
            # choose by highest confidence (or lowest dist)
            if best is None or conf > best["conf"]:
                best = {"user_id": uid, "dist": dist, "conf": conf}
        if best is None:
            return None
        # apply thresholds
        if best["conf"] >= CONFIDENCE_THRESHOLD and best["dist"] <= L2_THRESHOLD:
            return best
        return None

    def can_punch(self, user_id: int) -> bool:
        ts = self.last_punch_ts.get(user_id, 0)
        return (time.time() - ts) >= MIN_SECONDS_BETWEEN_PUNCHES

    def record_punch(self, user_id: int):
        self.last_punch_ts[user_id] = time.time()


def start_camera_realtime(engine: LiveAttendanceEngine, show_window: bool = True):
    """
    Starts webcam, compares embeddings, and returns list of punches made:
    Each time a match is made and passes cooldown -> engine.record_punch(uid) should be followed by DB write.
    """
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera")

    punches = []  # appended dicts: {"user_id":..., "conf":..., "dist":..., "timestamp":...}
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            emb = FaceRecognitionService.extract_from_array_bgr(frame)
            label = "No face"
            color = (0, 0, 255)
            if emb is not None:
                match = engine.match_embedding(emb)
                if match is not None:
                    uid = match["user_id"]
                    conf = match["conf"]
                    dist = match["dist"]
                    meta = engine.user_meta.get(uid, {})
                    username = meta.get("username", str(uid))
                    if engine.can_punch(uid):
                        # register in-memory and caller (management cmd) will persist to DB
                        engine.record_punch(uid)
                        punches.append({"user_id": uid, "conf": conf, "dist": dist, "timestamp": time.time(), "username": username})
                        label = f"Matched: {username} {conf:.2f}"
                        color = (0, 255, 0)
                    else:
                        label = f"Seen (cooldown): {username}"
                        color = (0, 255, 255)
                else:
                    label = "Face but no match"
                    color = (0, 0, 255)

            if show_window:
                cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.imshow("Live Attendance (press q to quit)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        cap.release()
        if show_window:
            cv2.destroyAllWindows()
    return punches
