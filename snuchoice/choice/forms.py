from django import forms
from .models import Answer, Question


class QuestionForm(forms.ModelForm):
    name = forms.CharField(max_length=30)

    class Meta:
        model = Question
        fields = ['title']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        if self.user.name:
            del self.fields['name']

    def clean_title(self):
        data = self.cleaned_data.get("title")
        if not data.endswith("."):
            raise forms.ValidationError("명제는 온점으로 끝나는 완결된 문장이어야 합니다.")
        return data

    def save(self, commit=True):
        if 'name' in self.fields:
            self.user.name = self.cleaned_data['name']
            self.user.save()
        return super().save(commit)


class AnswerForm(forms.ModelForm):

    class Meta:
        model = Answer
        fields = ['content']
