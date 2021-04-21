from django.urls import path
from . import views


urlpatterns = [
    path('quiz/', views.QuizAPIView.as_view(), name='quiz'),
    path('question/', views.QuestionAPIView.as_view(), name='question'),
    path('quiz/active/', views.ActiveQuizAPIView.as_view(), name='active_quiz'),
    path('quiz/create_answer/', views.QuizCreateAnswerAPIView.as_view(), name='active_answer'),
    path('visitor/answers/', views.VisitorHistoryAnswerAPIView.as_view(), name='active_answer'),
]
