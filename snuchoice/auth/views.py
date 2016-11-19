from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.http import Http404, JsonResponse
from django.shortcuts import render, resolve_url
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string
from django.views import generic
from snuchoice.core.mail import send_template_mail
from snuchoice.core.mixins import VerifyRequiredMixin
from .models import EmailConfirmKey
from .forms import EmailForm, SettingsForm


class EmailConfirmationView(generic.FormView):
    form_class = EmailForm
    template_name = 'auth/email_form.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        self.send_confirmation_email(email)

        if self.request.is_ajax():
            data = {
                'success': True,
                'msg': render_to_string('auth/confirmation_email_sent.txt', {'email': 'email'}),
            }

            return JsonResponse(data)

        else:
            self.template_name = 'auth/confirmation_email_sent.html'

            return super().render_to_response()

    def form_invalid(self, form):
        if self.request.is_ajax():
            template_name = 'auth/email_form_input.html'
            ctx = self.get_context_data(form=form, request=self.request)

            data = {
                'success': False,
                'html': render_to_string(template_name, ctx),
            }

            return JsonResponse(data)

        else:
            return super().form_invalid()

    def send_confirmation_email(self, email):
        confirm_key = get_random_string(length=64).lower()
        EmailConfirmKey.objects.create(email=email, key=confirm_key)
        ctx = {
            'url': self.request.build_absolute_uri(resolve_url("verify_signup", confirm_key)),
            'next': self.request.GET.get('next', ""),
        }
        send_template_mail("auth/email_contents.html", ctx, email)


confirm_email = EmailConfirmationView.as_view()


def get_user_through_email(email):
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        user = UserModel.objects.create_user(email=email)

    return user


def signup(request, key):
    # 이메일 컨퍼메이션 키 시간 제한 로직 추가해야함
    try:
        email_confirm_key = EmailConfirmKey.objects.get(key=key)
    except EmailConfirmKey.DoesNotExist:
        raise Http404('키 일치하는 유저 없음')

    user = get_user_through_email(email_confirm_key.email)
    form = SetPasswordForm(user, request.POST or None)

    ctx = {
        'form': form,
    }

    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)

        return render(request, 'auth/signup_success.html', ctx)

    else:
        return render(request, 'auth/signup_form.html', ctx)


class Settings(VerifyRequiredMixin, generic.UpdateView):
    form_class = SettingsForm
    template_name = "auth/settings.html"

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        kwargs.setdefault("password_form", PasswordChangeForm(self.get_object()))
        return super().get_context_data(**kwargs)


class DeleteAccount(VerifyRequiredMixin, generic.DeleteView):
    template_name = "auth/delete_account.html"
    success_url = reverse_lazy("home")

    def get_object(self):
        return self.request.user
