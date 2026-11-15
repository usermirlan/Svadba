import json

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import views as auth_views
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import InvitationForm
from .models import Invitation, Photo, Rsvp, validate_image_size

owner_required = staff_member_required(login_url="owner_login")
MAX_PHOTOS = 12


# ---------- коноктор көргөн бет ----------
def invitation(request, slug):
    inv = get_object_or_404(Invitation, slug=slug)
    if not inv.is_active and not request.user.is_staff:
        raise Http404
    og_image = request.build_absolute_uri(inv.cover_photo.url) if inv.cover_photo else ""
    return render(request, "inv/invite.html", {"inv": inv, "ts": int(inv.date.timestamp() * 1000), "og_image": og_image})


@require_POST
def rsvp(request, slug):
    inv = get_object_or_404(Invitation, slug=slug, is_active=True, show_rsvp=True)
    try:
        body = json.loads(request.body.decode("utf-8"))
        name = str(body.get("name", "")).strip()[:60]
        coming = bool(body.get("coming"))
        count = int(body.get("count", 1))
    except (ValueError, TypeError, UnicodeDecodeError):
        return JsonResponse({"ok": False}, status=400)
    if len(name) < 2 or not (1 <= count <= 10):
        return JsonResponse({"ok": False}, status=400)
    if inv.rsvps.count() >= 2000:
        return JsonResponse({"ok": False}, status=429)
    Rsvp.objects.create(invitation=inv, name=name, coming=coming, count=count if coming else 0)
    return JsonResponse({"ok": True})


def guests(request, slug, token):
    """Той ээси үчүн жашыруун шилтеме: келе тургандардын тизмеси."""
    inv = get_object_or_404(Invitation, slug=slug, token=token)
    rs = list(inv.rsvps.all())
    return render(request, "inv/guests.html", {"inv": inv, "rsvps": rs, "yes": sum(r.coming for r in rs), "no": sum(not r.coming for r in rs)})


# ---------- сатуучунун панели ----------
class OwnerLogin(auth_views.LoginView):
    template_name = "inv/owner/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or "/owner/"


@owner_required
def owner_list(request):
    invs = Invitation.objects.prefetch_related("rsvps")
    return render(request, "inv/owner/list.html", {"invs": invs})


def _save_photos(request, inv):
    files = request.FILES.getlist("photos")
    room = MAX_PHOTOS - inv.photos.count()
    field = forms.ImageField()
    added, bad = 0, 0
    for f in files[:max(room, 0)]:
        try:
            validate_image_size(f)
            field.clean(f)
            f.seek(0)
        except ValidationError:
            bad += 1
            continue
        Photo.objects.create(invitation=inv, image=f, order=inv.photos.count())
        added += 1
    if bad:
        messages.error(request, f"{bad} файл сүрөт эмес же өтө чоң, кошулган жок")
    if len(files) > room:
        messages.error(request, f"Эң көп {MAX_PHOTOS} сүрөт кошсо болот")
    return added


@owner_required
def owner_edit(request, pk=None):
    inv = get_object_or_404(Invitation, pk=pk) if pk else None
    form = InvitationForm(request.POST or None, request.FILES or None, instance=inv)
    if request.method == "POST" and form.is_valid():
        inv = form.save()
        _save_photos(request, inv)
        messages.success(request, "Чакыруу сакталды")
        return redirect("owner_edit", pk=inv.pk)
    return render(request, "inv/owner/form.html", {"form": form, "inv": inv})


@owner_required
@require_POST
def owner_photo_delete(request, pk):
    ph = get_object_or_404(Photo, pk=pk)
    inv_id = ph.invitation_id
    ph.image.delete(save=False)
    ph.delete()
    return redirect("owner_edit", pk=inv_id)


@owner_required
@require_POST
def owner_delete(request, pk):
    inv = get_object_or_404(Invitation, pk=pk)
    for ph in inv.photos.all():
        ph.image.delete(save=False)
    if inv.cover_photo:
        inv.cover_photo.delete(save=False)
    if inv.music:
        inv.music.delete(save=False)
    inv.delete()
    messages.success(request, "Чакыруу өчүрүлдү")
    return redirect("owner_list")
