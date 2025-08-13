from django.shortcuts import render
from django.contrib.auth.models import User
from library.models import Book

def home(request):
    # Statistik untuk ditampilkan di homepage
    context = {
        'total_books': Book.objects.count(),
        'total_users': User.objects.count(),
        'processed_books': Book.objects.filter(images_folder__isnull=False).count(),
        'total_genres': Book.objects.values('genre').distinct().count(),
        'recent_books': Book.objects.order_by('-created_at')[:4],  # 4 buku terbaru
    }

    return render(request, 'home.html', context)
