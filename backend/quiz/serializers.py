from rest_framework import serializers

from .models import *


class QuizSerializer(serializers.ModelSerializer):
    start = serializers.DateTimeField(format="%d.%m.%Y %H:%M")
    end = serializers.DateTimeField(format="%d.%m.%Y %H:%M")
    questions = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ('id', 'name', 'description', 'start', 'end', 'status', 'questions',)

    @staticmethod
    def get_questions(obj):
        questions = Question.objects.filter(quiz=obj.id, archived=False)
        return QuestionsSerializer(questions, many=True).data

    @staticmethod
    def get_status(obj):
        if obj.archived: status = 'Отправлен в архив'
        else: status = 'Активный'

        return status


class QuestionsSerializer(serializers.ModelSerializer):
    type_question_id = serializers.IntegerField(source='type_question.id')
    type_question_name = serializers.CharField(source='type_question')
    variable_answer = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('id', 'question', 'position', 'type_question_id', 'type_question_name', 'variable_answer')

    @staticmethod
    def get_variable_answer(obj):
        variable_answer = VariableAnswer.objects.filter(question=obj.id)
        return VariableAnswerSerializer(variable_answer, many=True).data


class VariableAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariableAnswer
        fields = ('id', 'text')


class HistoryAnswersSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question')
    variable_answer_text = serializers.SerializerMethodField()
    variable_answer_ids = serializers.SerializerMethodField()

    class Meta:
        model = UserAnswer
        fields = ('id', 'question', 'question_text', 'answer_text', 'variable_answer_ids', 'variable_answer_text')

    @staticmethod
    def get_variable_answer_ids(obj):
        return obj.variable_answer.values_list('id')

    @staticmethod
    def get_variable_answer_text(obj):
        variable_answer = VariableAnswer.objects.filter(id__in=obj.variable_answer.values_list('id'))
        return [_.text for _ in variable_answer]
