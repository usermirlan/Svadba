import os
import secrets

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
WEEKDAYS = ["дүйшөмбү", "шейшемби", "шаршемби", "бейшемби", "жума", "ишемби", "жекшемби"]
AUDIO_EXT = {".mp3", ".m4a", ".ogg", ".wav", ".aac"}


def new_slug():
    return secrets.token_urlsafe(6).replace("-", "a").replace("_", "b").lower()


def new_token():
    return secrets.token_urlsafe(16)


def validate_audio(f):
    if os.path.splitext(f.name)[1].lower() not in AUDIO_EXT:
        raise ValidationError("Музыка mp3, m4a, ogg, wav же aac форматында болушу керек")
    if f.size > 20 * 1024 * 1024:
        raise ValidationError("Музыка файлы 20 МБдан чоң болбошу керек")


def validate_image_size(f):
    if f.size > 10 * 1024 * 1024:
        raise ValidationError("Сүрөт 10 МБдан чоң болбошу керек")


class Invitation(models.Model):
    slug = models.SlugField(unique=True, default=new_slug, editable=False)
    token = models.CharField(max_length=40, default=new_token, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField("Жарыяланган", default=True)

    event_title = models.CharField("Тойдун түрү", max_length=60, default="Үйлөнүү тою",
                                   help_text="Мисалы: Үйлөнүү тою, Кыз узатуу, Юбилей")
    tagline = models.CharField("Башкы беттеги жазуу", max_length=80, default="Биз үйлөнүп жатабыз")
    name1 = models.CharField("Биринчи ат", max_length=30)
    name2 = models.CharField("Экинчи ат", max_length=30, blank=True, help_text="Бир киши болсо бош калтырыңыз")
    date = models.DateTimeField("Күнү жана убактысы")
    hosts = models.CharField("Той ээлери", max_length=120, blank=True, help_text="Мисалы: Бакыт жана Гүлнара")
    text = models.TextField("Чакыруу тексти", default="Сиздерди үйлөнүү тоюбузга арналган салтанаттуу дасторконубуздун кадырлуу коногу болууга чакырабыз.")
    program = models.TextField("Программа", blank=True, default="17:00 | Конокторду тосуу | Фуршет жана сүрөткө түшүү\n18:00 | Салтанаттын башталышы\n21:00 | Той торту жана бий",
                               help_text="Ар бир сапка: убакыт | аталышы | кошумча (милдеттүү эмес)")
    venue_name = models.CharField("Тойкананын аты", max_length=100)
    venue_address = models.CharField("Дареги", max_length=160, blank=True)
    map_url = models.URLField("2GIS шилтемеси", blank=True)
    show_rsvp = models.BooleanField("«Келесизби?» формасы", default=True)

    cover_photo = models.ImageField("Башкы сүрөт (фонго)", upload_to="covers/", blank=True, validators=[validate_image_size],
                                    help_text="Тик (вертикалдуу) сүрөт жакшы көрүнөт")
    music = models.FileField("Музыка", upload_to="music/", blank=True, validators=[validate_audio],
                             help_text="mp3 файл. Бош калса, жөнөкөй обон ойнойт")

    class Meta:
        ordering = ["-created"]
        verbose_name = "Чакыруу"
        verbose_name_plural = "Чакыруулар"

    def __str__(self):
        return self.title

    @property
    def title(self):
        return f"{self.name1} & {self.name2}" if self.name2 else self.name1

    @property
    def initials(self):
        return f"{self.name1[:1]}&{self.name2[:1]}" if self.name2 else self.name1[:1]

    @property
    def local(self):
        return timezone.localtime(self.date)

    @property
    def month_name(self):
        return MONTHS[self.local.month - 1]

    @property
    def weekday_name(self):
        return WEEKDAYS[self.local.weekday()]

    @property
    def program_items(self):
        out = []
        for line in self.program.splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2 and parts[1]:
                out.append({"time": parts[0], "title": parts[1], "note": parts[2] if len(parts) > 2 else ""})
        return out

    @property
    def coming_total(self):
        return sum(r.count for r in self.rsvps.all() if r.coming)


class Photo(models.Model):
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="photos/", validators=[validate_image_size])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class Rsvp(models.Model):
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE, related_name="rsvps")
    name = models.CharField(max_length=60)
    coming = models.BooleanField(default=True)
    count = models.PositiveSmallIntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
