from django import forms

from .models import Invitation


class KgFile(forms.ClearableFileInput):
    initial_text = 'Азыркы файл'
    input_text = 'Алмаштыруу'
    clear_checkbox_label = 'Өчүрүү'


class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ["event_title", "tagline", "name1", "name2", "date", "hosts", "text", "program",
                  "venue_name", "venue_address", "map_url", "cover_photo", "music", "show_rsvp", "is_active"]
        widgets = {
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "text": forms.Textarea(attrs={"rows": 3}),
            "program": forms.Textarea(attrs={"rows": 5}),
            "cover_photo": KgFile(attrs={"accept": "image/*"}),
            "music": KgFile(attrs={"accept": "audio/*,.mp3,.m4a"}),
        }

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields["date"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"]
        for f in self.fields.values():
            w = f.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = "chk"
            elif not isinstance(w, forms.ClearableFileInput):
                w.attrs["class"] = "inp"
