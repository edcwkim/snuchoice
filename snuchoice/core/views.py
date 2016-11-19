import itertools
import random
from django.db.models import Count
from django.views import generic
from snuchoice.choice.models import Question


class Home(generic.TemplateView):

    template_name = 'core/home.html'

    SLIDER_QUOTA = 5
    slider_question_list = None

    def dispatch(self, request, *args, **kwargs):
        self.slider_question_list = self.get_slider_question_list()  # to calculate only once
        return super().dispatch(request, *args, **kwargs)

    def get_slider_question_list(self):
        """
        공론화 게시물(역치 이상 공론화 버튼 눌린 게시물) 늘어가면서 초기 컨텐츠 개수 줄어듬.
        초기 컨텐츠의 중요도를 생각해서 표시될 초기 컨텐츠 갯수만큼 사전 결정된 순서로 추출해서 게시함.
        """
        qs = Question.objects.annotate(Count('votes'))
        slider_question_list = qs.filter(
            votes__count__gte=Question.THRESHOLD).order_by('-votes__count')
        if slider_question_list.count() < self.SLIDER_QUOTA:
            initial_question_list = qs.exclude(initial_order=0).filter(
                votes__count__lt=Question.THRESHOLD).order_by('initial_order')
            slider_question_list = list(itertools.chain(
                slider_question_list,
                initial_question_list
            ))[:self.SLIDER_QUOTA]
        else:
            slider_question_list = slider_question_list[:self.SLIDER_QUOTA]
        return slider_question_list

    def get_feed_question_list(self):
        excluding_ids = [question.id for question in self.slider_question_list]
        qs = Question.objects.exclude(id__in=excluding_ids).annotate(Count('votes'))
        weighted_shuffle = sorted(qs,
            key=lambda q: (q.votes__count + 1) * random.random(), reverse=True)
        return weighted_shuffle[:10]  # TODO: cache results

    def get_context_data(self, **kwargs):
        kwargs.setdefault("slider_question_list", self.slider_question_list)
        kwargs.setdefault("question_loop", self.get_feed_question_list())
        return super().get_context_data(**kwargs)
