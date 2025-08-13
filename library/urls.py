from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('add/', views.book_create, name='book_create'),
    path('<int:pk>/', views.book_detail, name='book_detail'),
    path('<int:pk>/preview/', views.book_preview, name='book_preview'),
    path('<int:pk>/reprocess/', views.reprocess_book, name='reprocess_book'),
    path('<int:pk>/analyze/', views.analyze_book, name='analyze_book'),
    path('<int:pk>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('edit/<int:pk>/', views.book_update, name='book_update'),
    path('delete/<int:pk>/', views.book_delete, name='book_delete'),
]
