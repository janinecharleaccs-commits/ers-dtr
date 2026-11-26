from django.urls import include, path

urlpatterns = [
    path("", include("dtr.urls")),
]
