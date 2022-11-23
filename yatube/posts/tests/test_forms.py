from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, User, Comment


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            image=uploaded
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormsTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormsTests.group.id,
            'image': PostFormsTests.post.image
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        post = Post.objects.order_by('-pk')[0]

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': PostFormsTests.user
            }))
        self.assertEqual(post_count + 1, Post.objects.count())
        self.assertEqual(
            form_data['group'], PostFormsTests.group.id
        )
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, PostFormsTests.user)

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
        post = Post.objects.get(id=PostFormsTests.post.id)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': PostFormsTests.post.id
            }
        ))
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], PostFormsTests.group1.id)
        self.assertEqual(post.author, PostFormsTests.user)
        self.assertEqual(post_count, Post.objects.count())

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
        comment = Comment.objects.order_by('-pk')[0]
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': PostFormsTests.post.id}
        ))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, PostFormsTests.user)
        self.assertEqual(comment.post, PostFormsTests.post)

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
