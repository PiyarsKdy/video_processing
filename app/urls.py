from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from app import views

urlpatterns = [
    path('', views.upload_video, name='upload_video'),
    path('videos/', views.video_list, name='video_list'),
    path('videos/<int:video_id>/', views.video_detail, name='video_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)