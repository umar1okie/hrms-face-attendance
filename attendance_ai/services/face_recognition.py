# attendance_ai/services/face_recognition.py
import os
from typing import List, Optional, Tuple
import numpy as np
import cv2
from PIL import Image
from insightface import app
from attendance_ai.utils.crypto import decrypt_array

# Singleton analyzer
_FACE_ANALYZER = None

def get_face_analyzer(det_size: Tuple[int,int]=(640,640)):
    """
    Lazily initialize InsightFace FaceAnalysis (CPU).
    """
    global _FACE_ANALYZER
    if _FACE_ANALYZER is None:
        # allowed_modules: detection + recognition
        _FACE_ANALYZER = app.FaceAnalysis(allowed_modules=['detection', 'recognition'])
        # ctx_id = -1 forces CPU; use ctx_id=0 for GPU if you have CUDA + onnxruntime-gpu
        _FACE_ANALYZER.prepare(ctx_id=-1, det_size=det_size)
    return _FACE_ANALYZER

def load_face_encoding_field(field):
    import numpy as np
    if field is None:
        return None
    if isinstance(field, list):
        return np.array(field, dtype=np.float32)
    if isinstance(field, str):
        try:
            lst = decrypt_array(field)
            return np.array(lst, dtype=np.float32)
        except Exception:
            # fallback if stored differently
            return None
    return None



class FaceRecognitionService:
    """
    InsightFace-based face recognition helpers.
    - embeddings are L2-normalized numpy float32 arrays (512-d).
    """

    @staticmethod
    def _load_image(path_or_array):
        """
        Accepts:
          - filepath (str) -> returns numpy RGB uint8 array
          - PIL.Image -> returns numpy RGB array
          - numpy ndarray -> return sanitized RGB numpy array
        """
        if isinstance(path_or_array, str):
            pil = Image.open(path_or_array).convert("RGB")
            return np.array(pil)
        if isinstance(path_or_array, Image.Image):
            return np.array(path_or_array.convert("RGB"))
        if isinstance(path_or_array, np.ndarray):
            arr = path_or_array
            # if BGR (from cv2), assume BGR and convert
            # we will let caller pass either BGR or RGB; attempt to detect:
            if arr.ndim == 3 and arr.shape[2] == 3:
                # dtype check
                if arr.dtype != np.uint8:
                    arr = (arr * 255).astype(np.uint8) if arr.max() <= 1.0 else arr.astype(np.uint8)
                # assume BGR if coming from cv2 usually (but caller should pass RGB)
                # To be safe: convert BGR -> RGB if user passes OpenCV frame (we expect BGR)
                # We'll detect likely BGR vs RGB by sampling values (not foolproof).
                # Simpler and reliable approach: if function used with cv2 frames, caller should call with BGR and
                # we convert to RGB in the usage functions below (get_embedding_from_array).
                return arr
            if arr.ndim == 2:
                # grayscale to RGB
                return cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
        raise ValueError("Unsupported image input type for FaceRecognitionService._load_image()")

    @staticmethod
    def detect_faces(image_input) -> List[dict]:
        """
        Detect faces and return list of detections.
        Each detection dict: {bbox:[x1,y1,x2,y2], score:float, raw: insightface.Face}
        Input: any accepted by _load_image (filepath, PIL, np.ndarray [RGB]).
        """
        img = FaceRecognitionService._load_image(image_input)
        analyzer = get_face_analyzer()
        faces = analyzer.get(img)
        results = []
        for f in faces:
            results.append({
                "bbox": [int(f.bbox[0]), int(f.bbox[1]), int(f.bbox[2]), int(f.bbox[3])],
                "score": float(getattr(f, "det_score", 0.0)),
                "raw": f
            })
        return results

    @staticmethod
    def extract_face_encoding(image_input, face_index: int = 0) -> Optional[np.ndarray]:
        """
        Extract normalized embedding from image (filepath or RGB numpy array).
        Returns None if no face detected.
        """
        img = FaceRecognitionService._load_image(image_input)
        analyzer = get_face_analyzer()
        faces = analyzer.get(img)
        if not faces:
            return None
        f = faces[face_index]
        emb = np.array(f.embedding, dtype=np.float32)
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb

    @staticmethod
    def extract_from_array_bgr(frame_bgr: np.ndarray, face_index: int = 0) -> Optional[np.ndarray]:
        """
        Helper to pass webcam frames (OpenCV BGR) directly.
        Returns normalized embedding or None.
        """
        # Convert BGR -> RGB
        if frame_bgr is None:
            return None
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        analyzer = get_face_analyzer()
        faces = analyzer.get(rgb)
        if not faces:
            return None
        f = faces[face_index]
        emb = np.array(f.embedding, dtype=np.float32)
        norm = np.linalg.norm(emb)
        return emb / norm if norm > 0 else emb

    @staticmethod
    def calculate_confidence(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Cosine similarity -> mapped to [0,1] as 'confidence'.
        """
        if emb1 is None or emb2 is None:
            return 0.0
        a = emb1 / (np.linalg.norm(emb1) + 1e-10)
        b = emb2 / (np.linalg.norm(emb2) + 1e-10)
        cos = float(np.dot(a, b))
        return (cos + 1.0) / 2.0

    @staticmethod
    def l2_distance(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Euclidean L2 distance (lower = more similar).
        """
        if emb1 is None or emb2 is None:
            return float("inf")
        return float(np.linalg.norm(emb1 - emb2))

    @staticmethod
    def basic_liveness_check(frames_bgr: List[np.ndarray]) -> Tuple[bool, str]:
        """
        Very simple motion based liveness: require pixel variance between frames.
        frames_bgr: list of OpenCV BGR frames (at least 2).
        """
        if not frames_bgr or len(frames_bgr) < 2:
            return False, "not_enough_frames"
        diffs = []
        for i in range(1, len(frames_bgr)):
            a = cv2.cvtColor(frames_bgr[i-1], cv2.COLOR_BGR2GRAY)
            b = cv2.cvtColor(frames_bgr[i], cv2.COLOR_BGR2GRAY)
            diffs.append(np.mean(np.abs(b.astype(np.float32) - a.astype(np.float32))))
        avg = float(np.mean(diffs))
        if avg < 2.0:
            return False, "no_motion_detected"
        return True, "ok"
