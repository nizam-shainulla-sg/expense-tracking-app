from django.urls import path

from . import views

urlpatterns = [
    path("", views.expense_list, name="expense_list"),
    path("add/", views.expense_add, name="expense_add"),
    path("register/", views.register, name="register"),
]
