from django import forms
from .models import User


class EmailForm(forms.Form):

    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email.split("@")[1] != "snu.ac.kr":
            raise forms.ValidationError("mySNU 이메일 주소를 입력해 주세요.")
        return email


class SettingsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = []
