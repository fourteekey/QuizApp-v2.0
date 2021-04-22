import json
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import TypeQuestion, Quiz, Question, UserAnswer, VariableAnswer
from .serializers import QuizSerializer, QuestionsSerializer


class CreatePromocodesCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        TypeQuestion.objects.create(name="Ответ текстом")
        TypeQuestion.objects.create(name="Выбрать ответ")
        TypeQuestion.objects.create(name="Выбрать несколько вариантов")
        author = get_user_model().objects.create(username='root', is_superuser=True)
        author.set_password('root')
        visitor = get_user_model().objects.create(username='visitor', is_superuser=False)
        visitor.set_password('visitor')
        quiz = Quiz.objects.create(name='Title', description='Description',
                                   start=datetime.strptime('12.02.2007 10:10', '%d.%m.%Y %H:%M'),
                                   end=datetime.strptime('12.02.2025 10:10', '%d.%m.%Y %H:%M'), author=author)
        questions = [
            {"text": "Напиши текст.", "type_question": 1},
            {"text": "Выбери ответ.", "type_question": 2, "variable_answer": ["Вариант1"]},
            {"text": "Выбери несколько ответов.", "type_question": 3, "variable_answer": ["Вариант1", "Вариант2"]}
        ]
        i = 0
        for question in questions:
            text = question.get('text', None)
            type_question_id = question.get('type_question', None)
            variable_answers = question.get('variable_answer', [])

            type_question = TypeQuestion.objects.filter(id=type_question_id)
            if type_question and (type_question_id == 1 or (type_question_id in (2, 3,) and variable_answers)):
                question = Question.objects.create(quiz=quiz, question=text, position=i, type_question=type_question[0])
                if type_question_id in (2, 3,):
                    for text_answer in variable_answers:
                        VariableAnswer.objects.create(text=text_answer, question=question)
                i += 1

    def setUp(self):
        self.author = get_user_model().objects.get(username='root')
        self.visitor = get_user_model().objects.get(username='visitor')
        self.quiz = Quiz.objects.get(id=1)

    def test_1_create_quiz(self):
        quiz_data = {'name': 'Title', 'description': 'Description', 'date_start': '12.02.2007 10:10',
                     'date_end': '12.02.2025 10:10'}
        response = self.client.post(f"/api/v1/quiz/?token={self.author.id}", data=quiz_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, QuizSerializer(Quiz.objects.last()).data)
        print('# Test "create quiz": OK')

    def test_2_update_quiz(self):
        print('Start Test "update quiz"')
        data = {'name': 'New Title', 'description': 'New description'}
        response = self.client.patch(f"/api/v1/quiz/?token={self.author.id}&quiz={self.quiz.id}", data)
        self.assertEqual(response.data, QuizSerializer(Quiz.objects.last()).data)
        print('# Test "update quiz": OK')

    def test_3_delete_quiz(self):
        print('Start Test "delete quiz"')
        response = self.client.delete(f"/api/v1/quiz/?token={self.author.id}&quiz={self.quiz.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(f"/api/v1/quiz/?token={self.author.id}&quiz={self.quiz.id}")
        self.assertEqual(response.data.get('status', None), 'Отправлен в архив')
        print('# Test "delete quiz": OK')

    def test_4_add_question(self):
        print('Start Test "add question"')
        data = {"questions": [
            {"text": "Тупой вопрос.", "type_question": 0},
            {"text": "Как зовут?", "type_question": 1},
            {"text": "Куда идешь?", "type_question": 2, "variable_answer": ["string"]},
            {"text": "Кто ты?", "type_question": 3, "variable_answer": ["string", "string3"]}
        ]}
        # В версиях 2.х и 3.х отличается сериализация их. поэтому и испольюзу dumps и content_type
        response = self.client.post(f"/api/v1/question/?token={self.author.id}&quiz={self.quiz.id}",
                                    data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, QuizSerializer(Quiz.objects.last()).data)
        print('# Test "add question": OK')

    def test_5_edit_question(self):
        print('Start Test "edit question"')
        data = {"questions": [
            {"text": "Как зовут?", "type_question": 1},
            {"text": "Куда идешь?", "type_question": 2, "variable_answer": ["string"]}]}

        # В версиях 2.х и 3.х отличается сериализация их. поэтому и испольюзу dumps и content_type
        self.client.post(f"/api/v1/question/?token={self.author.id}&quiz={self.quiz.id}",
                         data=json.dumps(data), content_type='application/json')

        # Меняем текст вопроса
        question = Question.objects.get(question='Как зовут?')
        response = self.client.patch(f"/api/v1/question/?token={self.author.id}&question={question.id}",
                                     data=json.dumps({"text": "Новый вопрос!"}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        list_key = [item['id'] for item in response.data.get('questions')]
        self.assertEqual(response.data.get('questions')[list_key.index(question.id)]['question'], 'Новый вопрос!')

        # Добавляем варианты ответа
        question = Question.objects.get(question='Куда идешь?')
        response = self.client.patch(f"/api/v1/question/?token={self.author.id}&question={question.id}",
                                     data=json.dumps({"variable_answer": ["string2"]}), content_type='application/json')
        serializer = QuestionsSerializer(question).data
        self.assertEqual(response.data['questions'][-1], serializer)
        self.assertEqual(len(serializer['variable_answer']), 2)
        print('# Test "edit question": OK')

    def test_6_get_active_quiz(self):
        print('Start Test "get active quiz"')
        response = self.client.get(f"/api/v1/quiz/active/?token={self.visitor.id}", content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, QuizSerializer([self.quiz], many=True).data)
        print('# Test "get active quiz": OK')


    def test_7_set_quiz_answer(self):
        print('Start Test "set answer to quiz"')
        answers = [{"id": 1, "text": "Ответ1"}, {"id": 2, "text": "Ответ не должен быть записан.", "variable": [1]}]
        # Ответ не на все вопросы
        response = self.client.post(f"/api/v1/quiz/create_answer/?token={self.visitor.id}&quiz={self.quiz.id}",
                                    data=json.dumps({"answers": answers}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('error', None), 'Не на все вопросы был предоставлен ответ.')
        # Ответ с неправильным вариантом
        answers.append({"id": 3, "variable": [5]})
        response = self.client.post(f"/api/v1/quiz/create_answer/?token={self.visitor.id}&quiz={self.quiz.id}",
                                    data=json.dumps({"answers": answers}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('error', None), 'Ответ на вопрос 3.\nВ списке отсутсвуют варианты ответов или есть неверные id.')
        # Записываем варианты ответа
        answers[2] = {"id": 3, "variable": [2, 3]}
        response = self.client.post(f"/api/v1/quiz/create_answer/?token={self.visitor.id}&quiz={self.quiz.id}",
                                    data=json.dumps({"answers": answers}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('detail', None), 'Ваши ответы записаны.')

        # Попытка повторного ответа на опросник
        response = self.client.post(f"/api/v1/quiz/create_answer/?token={self.visitor.id}&quiz={self.quiz.id}",
                                    data=json.dumps({"answers": answers}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('error', None), 'Вы уже проходили этот опрос или опрос недоступен.')
        print('# Test "set answer to quiz": OK')
        # Проверяем, что у пользователя есть ответ на опрос №1
        print('Start Test "Check answer to quiz": OK')
        response = self.client.get(f"/api/v1/visitor/answers/?token={self.visitor.id}", content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get('id', None), self.quiz.id)
        print('# Test "Check answer to quiz": OK')

