import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Тестовое описание',
        )
        cls.group1 = Group.objects.create(
            title='Тестовая группа1',
            slug='slug-test1',
            description='Тестовое описание1',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост больше, чем 15 символов',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormsTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small1.gif',
            content=small_gif,
            content_type='image/gif')
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormsTests.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': PostFormsTests.user
            }))
        self.assertEqual(post_count + 1, Post.objects.count())
        self.assertTrue(
            Post.objects.filter(
                group=PostFormsTests.group.id,
                text='Тестовый текст',
                author=PostFormsTests.user,
                image='posts/small1.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует пост"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст',
            'group': PostFormsTests.group1.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostFormsTests.post.id
            }),
            data=form_data
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': PostFormsTests.post.id
            }
        ))
        self.assertEqual(post_count, Post.objects.count())
        self.assertTrue(
            Post.objects.filter(
                group=PostFormsTests.group1.id,
                text='Новый текст',
                author=PostFormsTests.user,
                # image='posts/small.gif'
            ).exists()
        )

    def test_create_comment(self):
        """Валидная форма добавляет комментарий"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': PostFormsTests.post.id
            }),
            data=form_data
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': PostFormsTests.post.id}
        ))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Новый комментарий',
                author=PostFormsTests.user,
                post=PostFormsTests.post
            ).exists()
        )

    def test_create_comment_guest(self):
        """Валидная форма не создает комментарий от гостя"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий гостя'
        }
        self.client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': PostFormsTests.post.id
            }),
            data=form_data)
        self.assertEqual(Comment.objects.count(), comments_count)
