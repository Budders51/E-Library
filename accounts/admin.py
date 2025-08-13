from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Informasi User', {
            'fields': ('user',)
        }),
        ('Foto Profil', {
            'fields': ('photo',)
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
