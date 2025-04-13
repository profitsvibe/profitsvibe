from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Wallet


@receiver(post_save, sender=User)
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    """Create a UserProfile and Wallet instance for new users."""
    if created:
        UserProfile.objects.create(user=instance)
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile_and_wallet(sender, instance, **kwargs):
    """Save the UserProfile and Wallet instances when the User is saved."""
    instance.profile.save()
    instance.wallet.save()
