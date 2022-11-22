from django.test import TestCase

from ..models import Group, Post, User
from ..constants import NUMBER_OF_SYMBOLS


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост больше, чем 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        field = {
            str(
                PostModelTest.post
            ): PostModelTest.post.text[:NUMBER_OF_SYMBOLS],
            str(PostModelTest.group): PostModelTest.group.title
        }

        for value, expected_value in field.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected_value)

    def test_models_have_correct_verbos_name(self):
        """Проверяем, что в моделях корректно отображается verbos_name"""
        field_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'group': 'Группа'
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_models_have_correct_help_text(self):
        """Проверяем, что в моделях корректно отображается help_text"""
        post = PostModelTest.post
        field_help_text = {
            'group': 'Группа, к которой будет относиться пост'
        }

        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
