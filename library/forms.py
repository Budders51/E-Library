from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['file', 'title', 'description', 'author', 'year', 'genre', 'cover']
        widgets = {
            'file': forms.FileInput(attrs={'accept': 'application/pdf', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan judul buku'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Deskripsi buku'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama penulis'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tahun terbit'}),
            'genre': forms.Select(attrs={'class': 'form-control'}),
            'cover': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Urutan field sesuai spesifikasi: File, Judul, Deskripsi, Penulis, Tahun Terbit, Genre
        self.fields['file'].label = 'File PDF'
        self.fields['title'].label = 'Judul'
        self.fields['description'].label = 'Deskripsi'
        self.fields['author'].label = 'Penulis'
        self.fields['year'].label = 'Tahun Terbit'
        self.fields['genre'].label = 'Genre'
        self.fields['cover'].label = 'Cover Buku (Opsional)'
        self.fields['cover'].help_text = 'Jika tidak diupload, cover akan otomatis dibuat dari halaman pertama PDF'

class BookEditForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['file', 'title', 'description', 'author', 'year', 'genre']
        widgets = {
            'file': forms.FileInput(attrs={'accept': 'application/pdf', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan judul buku'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Deskripsi buku'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama penulis'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tahun terbit'}),
            'genre': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Untuk edit, field file menjadi opsional
        self.fields['file'].required = False
        self.fields['file'].label = 'File PDF (Upload file baru jika ingin mengganti)'
        self.fields['title'].label = 'Judul'
        self.fields['description'].label = 'Deskripsi'
        self.fields['author'].label = 'Penulis'
        self.fields['year'].label = 'Tahun Terbit'
        self.fields['genre'].label = 'Genre'
