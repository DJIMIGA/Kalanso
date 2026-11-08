from django.urls import path

from . import views

app_name = "core"

# Les chemins (visibles par les utilisateurs) sont en français ; les noms de routes en anglais.
urlpatterns = [
    path("", views.home, name="home"),
    path("sante/", views.health, name="health"),
    path("demo/heure/", views.demo_time, name="demo_time"),
]
