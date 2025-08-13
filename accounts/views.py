from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import UserProfileForm, CustomPasswordChangeForm, CustomRegistrationForm, CustomLoginForm
from .models import UserProfile

def register_view(request):
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Buat username dari email (bagian sebelum @)
            username = email.split('@')[0]

            # Pastikan username unik
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1

            # Buat user baru
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            messages.success(request, "Registrasi berhasil! Silakan login dengan email Anda.")
            return redirect('login')
    else:
        form = CustomRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Gunakan email sebagai username untuk authenticate
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('book_list')
            else:
                messages.error(request, "Email atau password salah.")
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    """Menampilkan profil user"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Hitung statistik untuk template
    processed_books_count = request.user.book_set.filter(images_folder__isnull=False).count()

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'processed_books_count': processed_books_count
    })

@login_required
def profile_edit(request):
    """Edit profil user"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # Redirect dengan parameter notifikasi untuk toast
            return redirect('/accounts/profile/?updated=profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})

@login_required
def change_password(request):
    """Ubah password user"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session agar user tidak logout setelah ganti password
            update_session_auth_hash(request, user)
            # Redirect dengan parameter notifikasi untuk toast
            return redirect('/accounts/profile/?updated=password')
        else:
            messages.error(request, 'Terjadi kesalahan. Periksa form di bawah.')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})
