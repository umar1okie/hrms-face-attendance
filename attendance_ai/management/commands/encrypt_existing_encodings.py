from django.core.management.base import BaseCommand
from attendance_ai.models import FaceProfile
from attendance_ai.utils.crypto import encrypt_array

class Command(BaseCommand):
    help = "Encrypt existing plaintext face encodings."

    def handle(self, *args, **options):
        qs = FaceProfile.objects.all()
        for p in qs:
            if isinstance(p.face_encoding, list):
                p.face_encoding = encrypt_array(p.face_encoding)
                p.save()
                self.stdout.write(f"Encrypted FaceProfile id={p.id}")
