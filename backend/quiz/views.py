from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from . import services


class QuizAPIView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True),
            openapi.Parameter('quiz', openapi.IN_QUERY, type='integer', description='Quiz id', required=True)
        ],
    )
    def get(self, request):
        quiz_id = request.query_params.get('quiz', None)

        if not quiz_id: return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                                        status=status.HTTP_400_BAD_REQUEST)

        quiz = services.get_quiz(quiz_id=quiz_id)
        if not quiz: return Response({'message': 'Опрос не найден.'}, status=status.HTTP_204_NO_CONTENT)
        return Response(quiz, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Максимум 100 символов.'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Максимум 1000 символов.'),
                'date_start': openapi.Schema(type=openapi.TYPE_STRING, description='Формат "dd.mm.yyyy"'),
                'date_end': openapi.Schema(type=openapi.TYPE_STRING, description='Формат "dd.mm.yyyy"'),
            })
    )
    def post(self, request):
        token = request.query_params.get('token', None)
        name = request.data.get('name', None)
        description = request.data.get('description', None)
        date_start = request.data.get('date_start', None)
        date_end = request.data.get('date_end', None)

        if not token or not name or not description or not date_start or not date_end:
            return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = services.check_user(token)
        if not user or not user.is_superuser:
            return Response({'error': 'Неверный токен пользователя или пользователь не является админом.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        quiz = services.create_quiz(name=name, description=description, date_start=date_start, date_end=date_end,
                                    author=user)
        if not quiz:
            return Response({'error': 'Даты введены неверно, проверьте формат и данные. Пример: \'02.12.2007 15:46\'.'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(quiz, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True),
            openapi.Parameter('quiz', openapi.IN_QUERY, type='integer', description='Quiz id', required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Максимум 100 символов.'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Максимум 1000 символов.'),
                'date_end': openapi.Schema(type=openapi.TYPE_STRING, description='Формат "dd.mm.yyyy"'),
            })
    )
    def patch(self, request):
        token = request.query_params.get('token', None)
        quiz_id = request.query_params.get('quiz', None)

        name = request.data.get('name', None)
        description = request.data.get('description', None)
        date_end = request.data.get('date_end', None)

        if not token or not quiz_id:
            return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = services.check_user(token)
        if not user or not user.is_superuser:
            return Response({'error': 'Неверный токен пользователя или пользователь не является админом.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        quiz = services.update_quiz(quiz_id=quiz_id, name=name, description=description, date_end=date_end,
                                    author=user)
        if not quiz and date_end:
            return Response({'error': 'Дата введена неверно, проверьте формат и данные. Пример: \'02.12.2007 15:46\'.'},
                            status=status.HTTP_400_BAD_REQUEST)
        elif not quiz:
            return Response({'error': 'ID не найден..'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(quiz, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True),
            openapi.Parameter('quiz', openapi.IN_QUERY, type='integer', description='Quiz id', required=True)
        ],
    )
    def delete(self, request):
        token = request.query_params.get('token', None)
        quiz_id = request.query_params.get('quiz', None)

        if not token or not quiz_id:
            return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = services.check_user(token)
        if not user or not user.is_superuser:
            return Response({'error': 'Неверный токен пользователя или пользователь не является админом.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        quiz = services.delete_quiz(quiz_id=quiz_id, author=user)
        if not quiz: return Response({'error': 'Опрос не найден.'}, status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_200_OK)


class QuestionAPIView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True),
            openapi.Parameter('quiz', openapi.IN_QUERY, type='integer', description='Quiz id', required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'questions': openapi.Schema(
                    type=openapi.TYPE_ARRAY, description='Список вопросов.',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'text': openapi.Schema(type=openapi.TYPE_STRING, description='Максимум 100 символов.'),
                            'type_question': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                            description='Тип ответа:\n'
                                                                        '<code>1 - Ответ текстом</code>'
                                                                        '<code>2 - Выбор одного варианта</code>'
                                                                        '<code>3 - Выбор нескольких вариантов.</code>'),
                            'variable_answer': openapi.Schema(type=openapi.TYPE_ARRAY,
                                                              description='Список вариантов ответа.',
                                                              items=openapi.Schema(type=openapi.TYPE_STRING))
                        })),
            }))
    def post(self, request):
        token = request.query_params.get('token', None)
        quiz_id = request.query_params.get('quiz', None)

        questions = request.data.get('questions', None)
        if not token or not quiz_id or not questions:
            return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = services.check_user(token)
        if not user or not user.is_superuser:
            return Response({'error': 'Неверный токен пользователя или пользователь не является админом.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        quiz = services.create_questions(quiz_id=quiz_id, questions=questions, author=user)
        if not quiz: return Response({'error': 'Опрос не найден.'}, status=status.HTTP_204_NO_CONTENT)

        return Response(quiz, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True),
            openapi.Parameter('question', openapi.IN_QUERY, type='integer', description='Question id', required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING, description='Максимум 100 символов.'),
                'type_question': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                description='Тип ответа:\n'
                                                            '<code>1 - Ответ текстом</code>'
                                                            '<code>2 - Выбор одного варианта</code>'
                                                            '<code>3 - Выбор нескольких вариантов.</code>'),
                'variable_answer': openapi.Schema(type=openapi.TYPE_ARRAY, description='Список вариантов ответа.',
                                                  items=openapi.Schema(type=openapi.TYPE_STRING))
            }))
    def patch(self, request):
        token = request.query_params.get('token', None)
        question_id = request.query_params.get('question', None)

        if not token or not question_id:
            return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = services.check_user(token)
        if not user or not user.is_superuser:
            return Response({'error': 'Неверный токен пользователя или пользователь не является админом.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        quiz = services.update_question(question_id=question_id, question=request.data, author=user)
        if not quiz: return Response({'error': 'Опрос не найден.'}, status=status.HTTP_204_NO_CONTENT)

        return Response(quiz, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True),
            openapi.Parameter('question', openapi.IN_QUERY, type='integer', description='Question id', required=True)
        ],
    )
    def delete(self, request):
        token = request.query_params.get('token', None)
        question_id = request.query_params.get('question', None)

        if not token or not question_id:
            return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = services.check_user(token)
        if not user or not user.is_superuser:
            return Response({'error': 'Неверный токен пользователя или пользователь не является админом.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        quiz = services.delete_question(question_id=question_id, author=user)
        if not quiz: return Response({'error': 'Опрос не найден.'}, status=status.HTTP_204_NO_CONTENT)

        return Response(quiz, status=status.HTTP_200_OK)


class ActiveQuizAPIView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True),
        ],
    )
    def get(self, request):
        token = request.query_params.get('token', None)

        if not token: return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                                      status=status.HTTP_400_BAD_REQUEST)

        user = services.check_user(token)
        if not user:
            return Response({'error': 'Неверный токен пользователя или пользователь не является админом.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        quiz = services.get_active_quiz(user)
        if not quiz: return Response({'message': 'Активных опросов нет.'}, status=status.HTTP_204_NO_CONTENT)
        return Response(quiz, status=status.HTTP_200_OK)


class QuizCreateAnswerAPIView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True),
            openapi.Parameter('quiz', openapi.IN_QUERY, type='integer', description='Quiz id', required=True)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'answers': openapi.Schema(
                    type=openapi.TYPE_ARRAY, description='Список Ответов.',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Question id ID'),
                            'text': openapi.Schema(type=openapi.TYPE_STRING, description='Максимум 100 символов.'),
                            'variable': openapi.Schema(type=openapi.TYPE_ARRAY,
                                                       description='Список id вариантов ответа.',
                                                       items=openapi.Schema(type=openapi.TYPE_INTEGER))
                        })),
            }))
    def post(self, request):
        token = request.query_params.get('token', None)
        quiz_id = request.query_params.get('quiz', None)
        if not token or not quiz_id: return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                                                     status=status.HTTP_400_BAD_REQUEST)
        answers = request.data.get('answers', None)
        if not isinstance(answers, list):
            return Response({'error': 'Проверьте формат'}, status=status.HTTP_400_BAD_REQUEST)

        user = services.check_user(token)
        if not user:
            return Response({'error': 'Неверный токен пользователя или пользователь не является админом.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        request_body, error = services.create_answer_quiz(quiz_id=quiz_id, answers=request.data, visitor=user)
        if error: return Response(request_body, status.HTTP_400_BAD_REQUEST)

        return Response(request_body, status=status.HTTP_200_OK)


class VisitorHistoryAnswerAPIView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type='string', description='User token', required=True),
        ],
    )
    def get(self, request):
        token = request.query_params.get('token', None)

        if not token: return Response({'error': 'В запросе отсутсвуют обязательные параметры.'},
                                      status=status.HTTP_400_BAD_REQUEST)

        user = services.check_user(token)
        if not user:
            return Response({'error': 'Неверный токен пользователя или пользователь не является админом.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        history_answers = services.get_history_answers(user)
        return Response(history_answers, status=status.HTTP_200_OK)
