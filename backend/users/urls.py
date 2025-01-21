from django.urls import path
from .views import RegisterView, LoginView, LogoutView, TestView

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("test", TestView.as_view(), name="test"),
]
