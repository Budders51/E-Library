from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Book, Favorite
from .forms import BookForm
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from .utils import convert_pdf_to_images, get_book_page_count, get_book_cover_from_pdf
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

def book_list(request):
    query = request.GET.get('q')
    genre = request.GET.get('genre')
    favorite = request.GET.get('favorite')

    books = Book.objects.all().order_by('-created_at')  # Tambahkan ordering

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(description__icontains=query) |
            Q(year__icontains=query)
        )

    if genre:
        books = books.filter(genre=genre)

    if favorite == '1':
        # Filter hanya buku yang difavoritkan oleh user saat ini
        books = books.filter(favorite__user=request.user)

    # Tambahkan pagination
    paginator = Paginator(books, 5)  # 5 buku per halaman
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get list favorit user untuk template
    user_favorites = []
    if request.user.is_authenticated:
        user_favorites = list(request.user.favorite_set.values_list('book_id', flat=True))

    return render(request, 'library/book_list.html', {
        'books': page_obj,
        'query': query,
        'page_obj': page_obj,
        'user_favorites': user_favorites
    })

@login_required
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.uploader = request.user
            book.save()

            # Proses konversi PDF ke gambar jika ada file PDF
            if book.file and book.file.name.endswith('.pdf'):
                try:
                    # Konversi PDF ke gambar
                    pdf_path = book.file.path
                    images_folder = convert_pdf_to_images(pdf_path, book.id)

                    if images_folder:
                        book.images_folder = images_folder

                    # Dapatkan jumlah halaman
                    page_count = get_book_page_count(pdf_path)
                    if page_count > 0:
                        book.pages = page_count

                    # Generate cover dari halaman pertama PDF
                    if not book.cover:
                        cover_path = get_book_cover_from_pdf(pdf_path, book.id)
                        if cover_path:
                            book.cover = cover_path

                    # Analisis otomatis untuk mendapatkan kata-kata relevan
                    try:
                        from .utils import analyze_book_text
                        keywords = analyze_book_text(pdf_path, max_keywords=5)
                        if keywords:
                            book.keywords = ', '.join(keywords)
                    except Exception as e:
                        pass

                    book.save()

                except Exception as e:
                    pass

            # Redirect dengan parameter notifikasi
            return redirect(f'/library/?uploaded={book.title}')
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form, 'title': 'Upload Buku'})


@login_required
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    # cek user atau staff
    if not (request.user.is_staff or book.uploader == request.user):
        messages.error(request, "Kamu tidak memiliki izin untuk mengedit buku ini.")
        return redirect('book_list')

    if request.method == 'POST':
        from .forms import BookEditForm
        form = BookEditForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            # Simpan data lama untuk perbandingan
            old_file = book.file

            # Simpan form
            updated_book = form.save()

            # Cek apakah file PDF berubah
            if 'file' in request.FILES and request.FILES['file'] != old_file:
                # File berubah, perlu diproses ulang
                # Hapus folder gambar lama jika ada
                if updated_book.images_folder:
                    import shutil
                    import os
                    from django.conf import settings

                    old_folder_path = os.path.join(settings.MEDIA_ROOT, updated_book.images_folder)
                    if os.path.exists(old_folder_path):
                        shutil.rmtree(old_folder_path)

                # Reset data terkait pemrosesan
                updated_book.images_folder = None
                updated_book.pages = None
                updated_book.cover = None
                updated_book.keywords = None
                updated_book.save()

                # Proses file PDF baru menggunakan fungsi yang tersedia
                try:
                    pdf_path = updated_book.file.path

                    # Konversi PDF ke gambar
                    images_folder = convert_pdf_to_images(pdf_path, updated_book.id)
                    if images_folder:
                        updated_book.images_folder = images_folder

                    # Dapatkan jumlah halaman
                    page_count = get_book_page_count(pdf_path)
                    if page_count > 0:
                        updated_book.pages = page_count

                    # Generate cover dari halaman pertama PDF
                    cover_path = get_book_cover_from_pdf(pdf_path, updated_book.id)
                    if cover_path:
                        updated_book.cover = cover_path

                    # Analisis otomatis untuk mendapatkan kata-kata relevan
                    try:
                        from .utils import analyze_book_text
                        keywords = analyze_book_text(pdf_path, max_keywords=5)
                        if keywords:
                            updated_book.keywords = ', '.join(keywords)
                    except Exception as e:
                        pass

                    updated_book.save()

                except Exception as e:
                    pass

            # Redirect dengan parameter notifikasi
            return redirect(f'/library/?edited={updated_book.title}')
    else:
        from .forms import BookEditForm
        form = BookEditForm(instance=book)

    return render(request, 'library/book_form.html', {
        'form': form,
        'title': 'Edit Buku',
        'book': book,
        'is_edit': True
    })


@login_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if not (request.user.is_staff or book.uploader == request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Kamu tidak memiliki izin untuk menghapus buku ini.'})
        messages.error(request, "Kamu tidak memiliki izin untuk menghapus buku ini.")
        return redirect('book_list')

    if request.method == 'POST' or request.method == 'DELETE':
        try:
            book_title = book.title
            book.delete()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Buku "{book_title}" berhasil dihapus.'})

            messages.success(request, f'Buku "{book_title}" berhasil dihapus.')
            return redirect('book_list')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Terjadi kesalahan saat menghapus buku.'})

            messages.error(request, 'Terjadi kesalahan saat menghapus buku.')
            return redirect('book_detail', pk=pk)

    # Jika GET request (untuk form konfirmasi)
    return render(request, 'library/book_confirm_delete.html', {'book': book})

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    # Check apakah buku ini sudah difavoritkan oleh user
    is_favorited = False
    if request.user.is_authenticated:
        from .models import Favorite
        is_favorited = Favorite.objects.filter(user=request.user, book=book).exists()

    return render(request, 'library/book_detail.html', {
        'book': book,
        'is_favorited': is_favorited
    })

def book_preview(request, pk):
    book = get_object_or_404(Book, pk=pk)

    # Pastikan buku memiliki images folder
    if not book.images_folder:
        messages.error(request, "Buku ini belum dikonversi ke gambar.")
        return redirect('book_detail', pk=pk)

    # Get page number dari URL parameter
    page_num = request.GET.get('page', 1)
    try:
        page_num = int(page_num)
    except ValueError:
        page_num = 1

    # Pastikan page number valid
    if page_num < 1:
        page_num = 1
    elif book.pages and page_num > book.pages:
        page_num = book.pages

    # Buat path ke gambar halaman
    image_filename = f"page_{page_num:03d}.png"
    image_path = f"{book.images_folder}/{image_filename}"

    # Check apakah file gambar ada
    full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)
    if not os.path.exists(full_image_path):
        messages.error(request, f"Halaman {page_num} tidak ditemukan.")
        return redirect('book_detail', pk=pk)

    context = {
        'book': book,
        'current_page': page_num,
        'total_pages': book.pages or 1,
        'image_url': f"{settings.MEDIA_URL}{image_path}",
        'has_previous': page_num > 1,
        'has_next': page_num < (book.pages or 1),
        'previous_page': page_num - 1 if page_num > 1 else None,
        'next_page': page_num + 1 if page_num < (book.pages or 1) else None,
    }

    return render(request, 'library/book_preview.html', context)

@login_required
@require_http_methods(["POST"])
def toggle_favorite(request, pk):
    """Toggle favorite status untuk buku via AJAX"""
    book = get_object_or_404(Book, pk=pk)

    try:
        # Coba cari existing favorite
        favorite = Favorite.objects.get(user=request.user, book=book)
        # Jika ada, hapus (unfavorite)
        favorite.delete()
        is_favorited = False
        message = "Buku dihapus dari favorit"
    except Favorite.DoesNotExist:
        # Jika tidak ada, tambah (favorite)
        Favorite.objects.create(user=request.user, book=book)
        is_favorited = True
        message = "Buku ditambahkan ke favorit"

    # Return JSON response untuk AJAX
    return JsonResponse({
        'success': True,
        'is_favorited': is_favorited,
        'message': message,
        'favorites_count': request.user.favorite_set.count()
    })

@login_required
def reprocess_book(request, pk):
    """
    Konversi ulang buku yang belum memiliki gambar
    """
    book = get_object_or_404(Book, pk=pk)

    # Cek permission
    if not (request.user.is_staff or book.uploader == request.user):
        messages.error(request, "Kamu tidak memiliki izin untuk memproses ulang buku ini.")
        return redirect('book_detail', pk=pk)

    # Proses konversi PDF ke gambar jika ada file PDF
    if book.file and book.file.name.endswith('.pdf'):
        try:
            # Konversi PDF ke gambar
            pdf_path = book.file.path
            images_folder = convert_pdf_to_images(pdf_path, book.id)

            if images_folder:
                book.images_folder = images_folder

            # Dapatkan jumlah halaman
            page_count = get_book_page_count(pdf_path)
            if page_count > 0:
                book.pages = page_count

            # Generate cover dari halaman pertama PDF jika belum ada cover
            if not book.cover:
                cover_path = get_book_cover_from_pdf(pdf_path, book.id)
                if cover_path:
                    book.cover = cover_path

            # Analisis otomatis jika belum ada keywords
            if not book.keywords:
                try:
                    from .utils import analyze_book_text
                    keywords = analyze_book_text(pdf_path, max_keywords=5)  # Batasi jadi 5 kata
                    if keywords:
                        book.keywords = ', '.join(keywords)
                        print(f"Debug: Auto-analysis completed during reprocess. Keywords: {book.keywords}")
                except Exception as e:
                    print(f"Debug: Auto-analysis failed during reprocess: {str(e)}")

            book.save()

            success_msg = f'Buku berhasil diproses ulang ({page_count} halaman)'
            if book.keywords:
                success_msg += ' dengan kata kunci relevan'
            messages.success(request, success_msg)

        except Exception as e:
            messages.error(request, f'Proses ulang buku gagal: {str(e)}')
    else:
        messages.error(request, 'File buku bukan PDF atau tidak ditemukan.')

    return redirect('book_detail', pk=pk)

@login_required
def analyze_book(request, pk):
    """
    Analisis teks buku untuk mendapatkan kata-kata relevan
    """
    book = get_object_or_404(Book, pk=pk)

    # Cek permission - hanya user yang login bisa menganalisis
    if not request.user.is_authenticated:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'message': 'Anda harus login untuk menganalisis buku.'})
        messages.error(request, "Anda harus login untuk menganalisis buku.")
        return redirect('book_detail', pk=pk)

    # Pastikan ada file PDF
    if not (book.file and book.file.name.endswith('.pdf')):
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'message': 'File buku bukan PDF atau tidak ditemukan.'})
        messages.error(request, 'File buku bukan PDF atau tidak ditemukan.')
        return redirect('book_detail', pk=pk)

    try:
        # Import fungsi analisis
        from .utils import analyze_book_text

        # Analisis teks dari PDF
        pdf_path = book.file.path
        keywords = analyze_book_text(pdf_path, max_keywords=5)  # Batasi jadi 5 kata

        if keywords:
            # Simpan keywords ke database
            book.keywords = ', '.join(keywords)
            book.save()

            # Return JSON response untuk AJAX request
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': f'Analisis berhasil! Ditemukan {len(keywords)} kata kunci relevan.',
                    'keywords': keywords,
                    'keywords_string': book.keywords
                })

            messages.success(request, f'Analisis berhasil! Ditemukan {len(keywords)} kata kunci relevan.')
        else:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'Tidak dapat mengekstrak kata kunci dari buku ini. Mungkin teks tidak dapat dibaca atau terlalu sedikit.'
                })
            messages.warning(request, 'Tidak dapat mengekstrak kata kunci dari buku ini. Mungkin teks tidak dapat dibaca atau terlalu sedikit.')

    except Exception as e:
        error_msg = f'Analisis gagal: {str(e)}'
        print(f"Debug: Analysis error = {str(e)}")

        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'message': error_msg})
        messages.error(request, error_msg)

    return redirect('book_detail', pk=pk)
