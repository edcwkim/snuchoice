from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^q/', include([
        url(r'^$', views.QuestionList.as_view(), name="question_list"),
        # url(r'^create/$', views.QuestionCreate.as_view(), name="question_create"),
        url(r'^vote/$', views.QuestionVote.as_view(), name="question_vote"),
    ])),
    url(r'^q/(?P<pk>\d+)/', include([
        url(r'^$', views.QuestionDetail.as_view(), name="question_detail"),
        # url(r'^delete/$', views.QuestionDelete.as_view(), name="question_delete"),
        # url(r'^answer/$', views.AnswerCreate.as_view(), name="answer_create"),
        # url(r'^answer/edit/$', views.AnswerUpdate.as_view(), name="answer_update"),
    ])),
    url(r'^p/(?P<pk>\d+)/$', views.PartyDetail.as_view(), name="party_detail"),
    url(r'^election-2016/$', views.ElectionList.as_view(), name="election_list"),
]
