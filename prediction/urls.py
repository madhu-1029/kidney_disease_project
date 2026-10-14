from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("predict/", views.predict, name="predict"),
    path("about/", views.about, name="about"),
    path("history/", views.history, name="history"),
    path("login/", views.user_login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.user_logout, name="logout"),
    path("history/delete/<int:history_id>/",views.delete_history,name="delete_history"),
]