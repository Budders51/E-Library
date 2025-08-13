from django.db import models
from django.contrib.auth.models import User
import os
import shutil
from django.conf import settings


class Book(models.Model):
    GENRE_CHOICES = [
        ('fiksi', 'Fiksi'),
        ('komik', 'Komik'),
        ('motivasi', 'Motivasi'),
    ]

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    year = models.IntegerField(null=True, blank=True, verbose_name="Tahun Terbit")
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, default='fiksi')
    pages = models.IntegerField(null=True, blank=True, verbose_name="Jumlah Halaman")
    keywords = models.TextField(blank=True, null=True, verbose_name="Kata-kata Relevan")

    cover = models.ImageField(upload_to='covers/', blank=True, null=True)
    file = models.FileField(upload_to='books/', null=True)
    images_folder = models.CharField(max_length=200, blank=True, null=True,
                                     help_text="Folder berisi gambar hasil konversi PDF")

    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        # Hapus file PDF
        if self.file:
            try:
                if os.path.isfile(self.file.path):
                    os.remove(self.file.path)
            except Exception as e:
                pass

        # Hapus cover
        if self.cover:
            try:
                if os.path.isfile(self.cover.path):
                    os.remove(self.cover.path)
            except Exception as e:
                pass

        # Hapus folder gambar beserta isinya
        if self.images_folder:
            try:
                folder_path = os.path.join(settings.MEDIA_ROOT, 'book_images', self.images_folder)
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                # Juga coba hapus folder tanpa 'book_images' prefix jika ada
                alt_folder_path = os.path.join(settings.MEDIA_ROOT, self.images_folder)
                if os.path.exists(alt_folder_path):
                    shutil.rmtree(alt_folder_path)
            except Exception as e:
                pass

        # Panggil method delete parent
        super().delete(*args, **kwargs)


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"