import itertools
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from snuchoice.core.mixins import VerifyRequiredMixin
from .forms import AnswerForm, QuestionForm
from .models import Answer, AnswerHistory, Election, Party, Press, Question, Vote


class QuestionList(generic.ListView):

    context_object_name = "question_loop"
    template_name = "choice/question_list.html"
    paginate_by = 10

    def get_queryset(self):
        return Question.objects.filter(initial_order=0).order_by('?')  # TODO: cache results


class QuestionDetail(generic.DetailView):

    model = Question
    context_object_name = "question"
    template_name = "choice/question_detail.html"

    def answers_by_party(self, show_only=None, stance=None, inverse=False):
        if show_only == "chong":
            parties = Party.objects.filter(election__college_order=0).order_by('?')
        elif show_only == "other":
            parties = Party.objects.exclude(election__college_order=0).order_by('?', 'election__college_order')
        else:
            parties = Party.objects.order_by('?')
            chong_parties = parties.filter(election__college_order=0)
            other_parties = parties.exclude(election__college_order=0)
            parties = list(itertools.chain(chong_parties, other_parties))

        answers_by_party = []
        unreplied_candidates = []
        for party in parties:
            answers = []
            for candidate in party.candidates.order_by("-_position"):
                answer_qs = Answer.objects.filter(question=self.object, candidate=candidate)
                answer_qs = answer_qs.filter(stance=stance) if stance is not None else answer_qs
                if answer_qs.exists():
                    answers.append(answer_qs.first())
                elif party.election == self.object.election or show_only == "force_all":
                    unreplied_candidates.append(candidate)
            if answers:
                answers_by_party.append((party, answers))

        if not inverse:
            return answers_by_party
        else:
            return unreplied_candidates

    def get_context_data(self, **kwargs):
        if self.object.initial_order:
            kwargs.setdefault("all_elections", True)
            kwargs.setdefault("college_elections", Election.get_college_elections())
            kwargs.setdefault("answers_by_party", self.answers_by_party(show_only="chong"))
            kwargs.setdefault("other_answers_by_party", self.answers_by_party(show_only="other"))
            kwargs.setdefault("unreplied_candidates", self.answers_by_party(show_only="force_all", inverse=True))
        else:
            kwargs.setdefault("all_elections", False)
            kwargs.setdefault("answers_by_party", self.answers_by_party())
            kwargs.setdefault("unreplied_candidates", self.answers_by_party(inverse=True))

        kwargs.setdefault("for_answers_by_party", self.answers_by_party(stance=True))
        kwargs.setdefault("aga_answers_by_party", self.answers_by_party(stance=False))
        kwargs.setdefault("votes_left", self.object.get_votes_left())
        return super().get_context_data(**kwargs)


class QuestionCreate(VerifyRequiredMixin, generic.CreateView):

    form_class = QuestionForm
    template_name = "choice/question_create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        college_elections = Election.objects.exclude(college_order=0).order_by("college_order")
        kwargs.setdefault("college_elections", college_elections)
        kwargs.setdefault("college_election", college_elections.filter(college_order=self.request.user.college_order).first())
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = self.request.user
        username = form.cleaned_data.get("name", "")
        if self.request.POST.get("chong") == "Y":
            college_order = 0
        else:
            college_order = user.college_order or self.request.POST.get("college_order")
        form.instance.election = Election.objects.filter(college_order=college_order).first()
        form.instance.author = user
        form.instance.author_name = username
        form.instance.author_email = user.email
        if college_order and not user.college_order:
            user.college_order = college_order
            user.college_order_fixed = True
            user.save()
        return super().form_valid(form)


class QuestionDelete(UserPassesTestMixin, generic.DeleteView):

    model = Question
    template_name = "choice/question_delete.html"
    success_url = reverse_lazy("home")

    def test_func(self):
        question = self.get_object()
        return self.request.user == question.author and not question.answers.count()


class QuestionVote(generic.View):

    def post(self, request, *args, **kwargs):
        question = get_object_or_404(Question, id=request.POST.get("id"))
        if request.is_ajax():
            data = {}
            if request.user.is_authenticated:
                try:
                    vote = Vote.objects.get(question=question, user=request.user)
                    vote.delete()
                except ObjectDoesNotExist:
                    Vote.objects.create(question=question, user=request.user)
            else:
                data['redirect'] = True
            return JsonResponse(data)
        else:
            if request.user.is_authenticated:
                try:
                    vote = Vote.objects.get(question=question, user=request.user)
                    vote.delete()
                except ObjectDoesNotExist:
                    Vote.objects.create(question=question, user=request.user)
                return redirect(request.META.get('HTTP_REFERER'))
            else:
                return redirect_to_login(request.get_full_path(), "verify")


class AnswerCreate(UserPassesTestMixin, generic.CreateView):

    form_class = AnswerForm
    template_name = "choice/answer_create.html"
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.is_candidate and not Answer.objects.filter(
            question=self.get_question(), candidate=user.candidate).exists()

    def get_question(self):
        return get_object_or_404(Question, pk=self.kwargs.get("pk"))

    def get_success_url(self):
        return self.object.question.get_absolute_url()

    def form_valid(self, form):
        stance = self.request.POST.get("stance")
        if stance == "T":
            form.instance.stance = True
        elif stance == "F":
            form.instance.stance = False
        else:
            form.instance.stance = None
        form.instance.question = self.get_question()
        form.instance.candidate = self.request.user.candidate
        form.instance.party = form.instance.candidate.party
        return super().form_valid(form)


class AnswerUpdate(UserPassesTestMixin, generic.UpdateView):

    form_class = AnswerForm
    template_name = "choice/answer_update.html"
    raise_exception = True

    def test_func(self):
        return self.request.user == self.get_object().candidate.user

    def get_object(self):
        question = get_object_or_404(Question, pk=self.kwargs.get("pk"))
        candidate = self.request.user.candidate
        return get_object_or_404(Answer, question=question, candidate=candidate)

    def get_success_url(self):
        return self.object.question.get_absolute_url()

    def form_valid(self, form):
        AnswerHistory.objects.create(answer=self.object,
            stance=self.object.stance, content=self.object.content)
        stance = self.request.POST.get("stance")
        if stance == "T":
            form.instance.stance = True
        elif stance == "F":
            form.instance.stance = False
        else:
            form.instance.stance = None
        return super().form_valid(form)


class PartyDetail(generic.DetailView):

    model = Party
    context_object_name = "party"
    template_name = "choice/party_detail.html"


class ElectionList(generic.ListView):

    model = Election
    context_object_name = "elections"
    template_name = "choice/election_list.html"
    ordering = "college_order"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("sub", Press.objects.filter(name__contains="SUB").first())
        kwargs.setdefault("news", Press.objects.filter(name__contains="신문").first())
        kwargs.setdefault("journal", Press.objects.filter(name__contains="저널").first())

        kwargs.setdefault("news_list", [
            ("http://www.snunews.com/news/articleView.html?idxno=16448", "당신의 이야기로 시작하는 총학생회 「U」"),
            ("http://www.snunews.com/news/articleView.html?idxno=16449", "위기의 대학, 당신의 대안 「더:하다」"),
            ("http://www.snunews.com/news/articleView.html?idxno=16450", "우리의 한마디가 서로에게 「닿음」"),
        ])
        kwargs.setdefault("journal_list", [
            ("http://www.snujn.com/news/27856", "'U' 선본 후보 인터뷰"),
            ("http://www.snujn.com/news/27871", "'더:하다' 선본 후보 인터뷰"),
            ("http://www.snujn.com/news/27874", "'닿음' 선본 후보 인터뷰"),
        ])
        return super().get_context_data(**kwargs)
