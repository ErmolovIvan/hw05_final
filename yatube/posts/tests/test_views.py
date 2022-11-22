import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Post, Group, User, Comment, Follow
from ..constants import NUMBER_OF_POSTS, NUMBER_OF_SYMBOLS_2ND_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
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
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Текст комментария'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': PostViewsTests.group.slug
            }): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': PostViewsTests.user.username
            }): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': PostViewsTests.post.id
            }): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': PostViewsTests.post.id
            }): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        index_author = first_object.author
        index_text = first_object.text
        index_group = first_object.group
        index_post_id = first_object.id
        index_image = first_object.image
        self.assertEqual(index_author, PostViewsTests.post.author)
        self.assertEqual(index_text, PostViewsTests.post.text)
        self.assertEqual(index_group, PostViewsTests.post.group)
        self.assertEqual(index_post_id, PostViewsTests.post.id)
        self.assertEqual(index_image, PostViewsTests.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list', kwargs={
                    'slug': PostViewsTests.group.slug
                }
            )
        )
        group_list_context = response.context.get('group')
        post_context = response.context['page_obj'][0]
        post_author = post_context.author
        post_text = post_context.text
        post_group = post_context.group
        post_post_id = post_context.id
        post_image = post_context.image
        self.assertEqual(group_list_context.title, PostViewsTests.group.title)
        self.assertEqual(group_list_context.slug, PostViewsTests.group.slug)
        self.assertEqual(
            group_list_context.description, PostViewsTests.group.description
        )
        self.assertEqual(post_author, PostViewsTests.post.author)
        self.assertEqual(post_text, PostViewsTests.post.text)
        self.assertEqual(post_group, PostViewsTests.post.group)
        self.assertEqual(post_post_id, PostViewsTests.post.id)
        self.assertEqual(post_image, PostViewsTests.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={
                    'username': PostViewsTests.post.author
                }
            )
        )
        profile_context = response.context.get('author')
        post_context = response.context['page_obj'][0]
        post_author = post_context.author
        post_text = post_context.text
        post_group = post_context.group
        post_post_id = post_context.id
        post_image = post_context.image
        self.assertEqual(profile_context, PostViewsTests.post.author)
        self.assertEqual(post_author, PostViewsTests.post.author)
        self.assertEqual(post_text, PostViewsTests.post.text)
        self.assertEqual(post_group, PostViewsTests.post.group)
        self.assertEqual(post_post_id, PostViewsTests.post.id)
        self.assertEqual(post_image, PostViewsTests.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': PostViewsTests.post.id
                }
            )
        )
        post_detail_context = response.context.get('post')
        post_context = response.context['post']
        post_author = post_context.author
        post_text = post_context.text
        post_group = post_context.group
        post_post_id = post_context.id
        post_image = post_context.image
        comment = post_context.comments.last()
        self.assertEqual(post_detail_context, PostViewsTests.post)
        self.assertEqual(post_author, PostViewsTests.post.author)
        self.assertEqual(post_text, PostViewsTests.post.text)
        self.assertEqual(post_group, PostViewsTests.post.group)
        self.assertEqual(post_post_id, PostViewsTests.post.id)
        self.assertEqual(post_image, PostViewsTests.post.image)
        self.assertEqual(comment, PostViewsTests.comment)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit', kwargs={
                    'post_id': PostViewsTests.post.pk
                }
            )
        )
        field_form = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in field_form.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context['post'].id, PostViewsTests.post.id)
        self.assertEqual(
            str(response.context['post']),
            PostViewsTests.post.text
        )

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        field_form = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in field_form.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_page_one_paginator(self):
        """На первой странице отображается правильное количество постов"""
        cache.clear()
        posts = []
        for i in range(1, 13):
            post = Post(
                author=PostViewsTests.post.author,
                text='Тест' + str(i),
                group=PostViewsTests.group,
            )
            posts.append(post)
        Post.objects.bulk_create(posts)
        pages = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list', kwargs={
                    'slug': PostViewsTests.group.slug
                }
            ),
            'profile': reverse(
                'posts:profile', kwargs={
                    'username': PostViewsTests.post.author
                }
            )
        }

        for page_name, page in pages.items():
            with self.subTest(page_name=page_name):
                response_page_1 = self.authorized_client.get(page)
                self.assertEqual(
                    len(response_page_1.context['page_obj']), NUMBER_OF_POSTS
                )

    def test_page_two_paginator(self):
        """На второй странице отображается правильное количество постов"""
        posts = []
        for i in range(1, 13):
            post = Post(
                author=PostViewsTests.post.author,
                text='Тест' + str(i),
                group=PostViewsTests.group,
            )
            posts.append(post)
        Post.objects.bulk_create(posts)
        pages = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list', kwargs={
                    'slug': PostViewsTests.group.slug
                }
            ),
            'profile': reverse(
                'posts:profile', kwargs={
                    'username': PostViewsTests.post.author
                }
            )
        }

        for page_name, page in pages.items():
            with self.subTest(page_name=page_name):
                response_page_2 = self.authorized_client.get(page + '?page=2')
                self.assertEqual(
                    len(response_page_2.context['page_obj']),
                    NUMBER_OF_SYMBOLS_2ND_PAGE
                )

    def post_exist_on_page(self):
        """Проверка существует ли созданный пост на странице"""
        post = Post.objects.create(
            author=PostViewsTests.post.author,
            text='Тест',
            group=PostViewsTests.group,
        )
        pages = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list', kwargs={
                    'slug': PostViewsTests.group.slug
                }
            ),
            'profile': reverse(
                'posts:profile', kwargs={
                    'username': PostViewsTests.post.author
                }
            )
        }

        for page_name, page in pages.items():
            with self.subTest(page_name=page_name):
                response = self.authorized_client.get(page)
                self.assertEqual(response.context['page_obj'][0], post)

    def test_new_post_not_in_another_group(self):
        """Пост не сохраняется в группе, не предназначенной для него."""
        post = Post.objects.create(
            text='Какой-то текст',
            author=PostViewsTests.user,
            group=PostViewsTests.group1,
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list', kwargs={
                    'slug': PostViewsTests.group.slug
                }
            )
        )
        self.assertNotIn(post, response.context["page_obj"].object_list)


    def test_index_cache(self):
        """Тест кэша главной страницы"""
        new_post = Post.objects.create(
            author=PostViewsTests.user,
            text='Тестовый пост для кэша',
            group=PostViewsTests.group,
        )
        response1 = self.authorized_client.get(reverse('posts:index'))
        response1_content = response1.content
        new_post.delete()
        response2 = self.authorized_client.get(reverse('posts:index'))
        response2_content = response2.content
        self.assertEqual(response1_content, response2_content)
        cache.clear()
        response3 = self.authorized_client.get(reverse('posts:index'))
        response3_content = response3.content
        self.assertNotEqual(response2_content, response3_content)

    def test_follow(self):
        """Тест подписки"""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='newauthor')
        self.authorized_client.get(reverse('posts:profile_follow', kwargs={
            'username': new_author.username
        }))
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, new_author)
        self.assertEqual(follow.user, PostViewsTests.user)

    def test_unfollow(self):
        """Тест отписки"""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='newauthor')
        self.authorized_client.get(reverse('posts:profile_follow', kwargs={
            'username': new_author.username
        }))
        self.authorized_client.get(reverse('posts:profile_unfollow', kwargs={
            'username': new_author.username
        }))
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_follow_index(self):
        """Тест появления новой записи в подписках"""
        new_user = User.objects.create_user(username="newauthor")
        new_client = Client()
        new_client.force_login(new_user)
        new_client.post(
            reverse(
                "posts:profile_follow",
                kwargs={"username": str(PostViewsTests.user)},
            )
        )
        new_post = Post.objects.create(
            author=PostViewsTests.user,
            text="Тест записи в подписках",
        )
        response = self.authorized_client.get(reverse("posts:follow_index"))
        response_new_user = new_client.get(reverse("posts:follow_index"))
        self.assertIn(new_post,
                      response_new_user.context["page_obj"].object_list)
        self.assertNotIn(new_post, response.context["page_obj"].object_list)
