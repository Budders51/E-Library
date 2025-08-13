from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import UserProfile
import re

class CustomRegistrationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Konfirmasi Password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Email'
        self.fields['password'].label = 'Password'
        self.fields['confirm_password'].label = 'Konfirmasi Password'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email sudah digunakan!")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')

        # Validasi minimal 8 karakter
        if len(password) < 8:
            raise ValidationError("Password minimal 8 karakter.")

        # Validasi harus ada huruf besar
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password harus mengandung minimal 1 huruf besar.")

        # Validasi harus ada huruf kecil
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password harus mengandung minimal 1 huruf kecil.")

        # Validasi harus ada angka
        if not re.search(r'\d', password):
            raise ValidationError("Password harus mengandung minimal 1 angka.")

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Password dan konfirmasi password tidak sama!")

        return cleaned_data

class CustomLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Email'
        self.fields['password'].label = 'Password'

class UserProfileForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = UserProfile
        fields = ['photo']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

        self.fields['photo'].label = 'Foto Profil'
        self.fields['username'].label = 'Username'
        self.fields['email'].label = 'Email'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Cek apakah username sudah digunakan user lain
        if User.objects.filter(username=username).exclude(id=self.instance.user.id).exists():
            raise ValidationError("Username sudah digunakan!")
        return username

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Update User model fields
            profile.user.username = self.cleaned_data['username']
            profile.user.email = self.cleaned_data['email']
            profile.user.save()
            profile.save()
        return profile

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        # Customize labels
        self.fields['old_password'].label = 'Password Lama'
        self.fields['new_password1'].label = 'Password Baru'
        self.fields['new_password2'].label = 'Konfirmasi Password Baru'

        # Add placeholders
        self.fields['old_password'].widget.attrs['placeholder'] = 'Masukkan password lama'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Masukkan password baru'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Konfirmasi password baru'
