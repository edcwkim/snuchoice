from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from snuchoice.choice.models import Candidate, Press


class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    name = models.CharField(_('full name'), max_length=30, blank=True)
    college_order = models.PositiveSmallIntegerField(_('collge id'), default=0)  # 단과대학 번호
    college_order_fixed = models.BooleanField(default=False)
    hide_other_collges = models.BooleanField(default=False)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    # queryset filter 검색 용이하게 하기 위해 따로 필드 설정하였음.
    is_candidate = models.BooleanField(default=False)
    is_journalist = models.BooleanField(default=False)
    candidate = models.OneToOneField(Candidate, blank=True, null=True)
    press = models.ForeignKey(Press, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        return self.name or self.email

    def get_short_name(self):
        return self.name or self.email

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)


@receiver(models.signals.pre_save, sender=User)
def set_boolean_fields(sender, instance, **kwargs):
    instance.is_candidate = bool(instance.candidate_id)
    instance.is_journalist = bool(instance.press_id)


class EmailConfirmKey(models.Model):
    email = models.EmailField()
    key = models.CharField(max_length=64, unique=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{0}. {1}'.format(self.pk, self.email)


@receiver(models.signals.pre_save, sender=EmailConfirmKey)
def clear_old_confirm_key(sender, instance, **kwargs):
    old_keys = EmailConfirmKey.objects.filter(email=instance.email)
    if old_keys.exists():
        old_keys.delete()
