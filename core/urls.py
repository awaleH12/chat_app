from . import views
from django.urls import path

urlpatterns = [
    path('', views.profile_view, name='profile_view'),
    path('create/', views.create_profile, name='create_profile'),
    path('delete/<int:pk>/', views.delete_profile, name='delete_profile'),
    path('profile/<int:pk>/', views.view_profile, name='view_profile'),
    path('profile/<int:pk>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:pk>/react/', views.react_profile, name='react_profile'),
    path('me/', views.my_profile, name='my_profile'),
    path('settings/', views.profile_settings, name='profile_settings'),
]
