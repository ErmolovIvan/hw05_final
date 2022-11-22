from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост больше, чем 15 символов',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_url_guest(self):
        """Тест доступности страниц для неавторизированного пользователя"""
        urls = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostURLTests.user}/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.id}/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{PostURLTests.post.id}/edit/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }

        for url, status_code in urls.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_url_user(self):
        """Тест доступности страниц для авторизированного пользователя"""
        urls = {
            f'/posts/{PostURLTests.post.id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK
        }

        for url, status_code in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_url_redirect_guest(self):
        """Тест перенаправления неавторизированного пользователя"""
        urls = {
            '/create/': reverse('users:login') + '?next='
            + reverse('posts:post_create'),
            f'/posts/{PostURLTests.post.id}/edit/':
            reverse('users:login') + '?next=' + reverse(
                'posts:post_edit', kwargs={
                    'post_id': PostURLTests.post.id
                }
            )
        }

        for url, redirect_url in urls.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_uls_uses_correct_tamplates(self):
        """Тест использования правильных шаблонов страниц"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }

        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_url_redirect_not_author(self):
        """Тест редиректа, если пользователь не автор"""
        user_not_author = User.objects.create_user(username='not_author')
        post = Post.objects.create(
            text='Тестовый текст',
            author=user_not_author
        )
        response = self.authorized_client.get(
            f'/posts/{post.id}/edit/'
        )
        self.assertRedirects(response, f'/posts/{post.id}/')
