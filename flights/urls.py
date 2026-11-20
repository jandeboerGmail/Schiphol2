from django.shortcuts import redirect
from django.urls import path

from . import views

urlpatterns = [
    path("", lambda request: redirect("board", direction="departures")),
    path("api/<str:direction>/", views.board_json, name="board_json"),
    path("<str:direction>/", views.board, name="board"),
]
