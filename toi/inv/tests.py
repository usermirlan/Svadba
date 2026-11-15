import io
import json
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from .models import Invitation

TMP = tempfile.mkdtemp()


def img(name="a.jpg"):
    b = io.BytesIO()
    Image.new("RGB", (60, 80), (140, 47, 69)).save(b, "JPEG")
    return SimpleUploadedFile(name, b.getvalue(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=TMP)
class InvTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP, ignore_errors=True)

    def setUp(self):
        User.objects.create_user("o", password="Toi-test-123", is_staff=True)
        self.data = {"event_title": "Үйлөнүү тою", "tagline": "Биз үйлөнүп жатабыз", "name1": "Азамат", "name2": "Айгерим",
                     "date": (timezone.localtime() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M"), "hosts": "Бакыт",
                     "text": "Келиңиздер", "program": "17:00 | Тосуу | Фуршет\n18:00 | Башталышы", "venue_name": "Ак-Ордо",
                     "venue_address": "Ош", "map_url": "", "show_rsvp": "on", "is_active": "on"}

    def create(self, **files):
        self.client.login(username="o", password="Toi-test-123")
        r = self.client.post("/owner/new/", {**self.data, **files})
        self.assertEqual(r.status_code, 302, r.context["form"].errors if r.context else "")
        return Invitation.objects.get()

    def test_owner_requires_login(self):
        self.assertEqual(self.client.get("/owner/").status_code, 302)
        self.assertEqual(self.client.get("/owner/new/").status_code, 302)

    def test_create_with_media_and_view(self):
        mp3 = SimpleUploadedFile("song.mp3", b"ID3" + b"\0" * 500, content_type="audio/mpeg")
        inv = self.create(cover_photo=img("c.jpg"), music=mp3, photos=[img("1.jpg"), img("2.jpg")])
        self.assertEqual(inv.photos.count(), 2)
        self.assertTrue(inv.cover_photo and inv.music)
        self.client.logout()
        r = self.client.get(f"/i/{inv.slug}/")
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        for part in ["Азамат", "Айгерим", "bgimg", 'id="bgm"', 'id="gal"', "Тосуу", "Ак-Ордо"]:
            self.assertIn(part, html)
        self.assertEqual(self.client.get("/owner/").status_code, 302)

    def test_rejects_bad_files(self):
        self.client.login(username="o", password="Toi-test-123")
        bad = SimpleUploadedFile("x.exe", b"MZ" * 50)
        r = self.client.post("/owner/new/", {**self.data, "music": bad})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Invitation.objects.count(), 0)
        inv = self.create(photos=[SimpleUploadedFile("fake.jpg", b"not an image")])
        self.assertEqual(inv.photos.count(), 0)

    def test_rsvp_and_guest_list(self):
        inv = self.create()
        self.client.logout()
        post = lambda b: self.client.post(f"/i/{inv.slug}/rsvp/", json.dumps(b), content_type="application/json")
        self.assertEqual(post({"name": "Нурлан", "coming": True, "count": 3}).status_code, 200)
        self.assertEqual(post({"name": "Айбек", "coming": False, "count": 2}).status_code, 200)
        self.assertEqual(post({"name": "", "coming": True, "count": 1}).status_code, 400)
        self.assertEqual(post({"name": "Көп", "coming": True, "count": 99}).status_code, 400)
        inv.refresh_from_db()
        self.assertEqual(inv.coming_total, 3)
        self.assertEqual(self.client.get(f"/i/{inv.slug}/guests/wrong/").status_code, 404)
        r = self.client.get(f"/i/{inv.slug}/guests/{inv.token}/")
        self.assertContains(r, "Нурлан")

    def test_hidden_invitation_and_no_name2(self):
        self.data["name2"] = ""
        self.data.pop("is_active")
        inv = self.create()
        self.assertEqual(self.client.get(f"/i/{inv.slug}/").status_code, 200)  # staff sees
        self.client.logout()
        self.assertEqual(self.client.get(f"/i/{inv.slug}/").status_code, 404)

    def test_delete(self):
        inv = self.create(cover_photo=img(), photos=[img()])
        self.client.post(f"/owner/{inv.pk}/delete/")
        self.assertEqual(Invitation.objects.count(), 0)
