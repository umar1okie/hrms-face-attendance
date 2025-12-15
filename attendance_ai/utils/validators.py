# attendance_ai/utils/validators.py
import imghdr

ALLOWED_EXTS = ("jpeg", "png", "jpg")
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB default

def validate_image_file(file_obj):
    # file_obj: Django UploadedFile
    if file_obj.size > MAX_SIZE_BYTES:
        return False, f"File too large (> {MAX_SIZE_BYTES} bytes)."
    # Check header via imghdr (safer than extension alone)
    file_obj.seek(0)
    kind = imghdr.what(None, h=file_obj.read(512))
    file_obj.seek(0)
    if not kind or kind.lower() not in ALLOWED_EXTS:
        return False, "Unsupported image format. Allowed: jpg, jpeg, png."
    return True, "OK"
