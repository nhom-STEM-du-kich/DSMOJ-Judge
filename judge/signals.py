from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # CHỈ TẠO KHI ĐÓ LÀ USER MỚI TINH (Lúc createsuperuser hoặc Register)
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Đảm bảo Profile luôn tồn tại trước khi save để tránh Crash Metadata
    if hasattr(instance, 'profile'):
        instance.profile.save()