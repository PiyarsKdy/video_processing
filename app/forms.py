from django import forms
from .models import Video

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'video_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'video_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
