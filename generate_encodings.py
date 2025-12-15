import os
import django
import cv2
import numpy as np
from insightface.app import FaceAnalysis

# -----------------------------
# Load Django Settings
# -----------------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from attendance_ai.models import User, FaceProfile


# -----------------------------
# Generate embedding using InsightFace
# -----------------------------
def generate_embedding(image_path, app):
    img = cv2.imread(image_path)

    if img is None:
        print(f"[ERROR] Cannot read image: {image_path}")
        return None

    faces = app.get(img)

    if len(faces) == 0:
        print(f"[ERROR] No face found in: {image_path}")
        return None

    return faces[0].embedding.tolist()


# -----------------------------
# Main Execution
# -----------------------------
def run():
    print("🚀 Starting InsightFace Encoding Generator...")

    # Initialize InsightFace model
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=0, det_size=(640, 640))

    # Correct base directory for known_faces
    project_root = os.path.dirname(os.path.abspath(__file__))  # D:\hrms-face-attendance
    known_faces_dir = os.path.join(project_root, "attendance_ai", "known_faces")

    print("🔍 Known faces directory:", known_faces_dir)

    # Process all users
    users = User.objects.all()

    for user in users:
        folder = os.path.join(known_faces_dir, user.username)

        print("👉 Checking folder:", folder)

        if not os.path.exists(folder):
            print(f"[SKIP] No folder found for user: {user.username}")
            continue

        # Scan all image files
        for file_name in os.listdir(folder):
            image_path = os.path.join(folder, file_name)

            if not image_path.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            print(f"➡️ Processing: {image_path}")

            embedding = generate_embedding(image_path, app)

            if embedding is None:
                continue

            # Store embedding in DB
            FaceProfile.objects.update_or_create(
                user=user,
                defaults={
                    "face_encoding": embedding,
                    "encoding_version": "insightface_v1",
                    "consent_given": True,
                    "is_active": True,
                }
            )

            print(f"✅ Saved embedding for: {user.username}")

    print("🎉 All embeddings generated successfully!")


# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    run()
