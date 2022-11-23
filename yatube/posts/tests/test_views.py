import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Post, Group, User, Comment, Follow
from ..constants import NUMBER_OF_POSTS, NUMBER_OF_SYMBOLS_2ND_PAGE
from ..forms import CommentForm, PostForm

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

    def post_check(self, context):
        """Метод проверки поста на странице"""
        if 'page_obj' in context:
            post = context['page_obj'][0]
        else:
            post = context['post']
        author = post.author
        text = post.text
        image = post.image
        group = post.group
        comment = post.comments.last()
        self.assertEqual(author, PostViewsTests.user)
        self.assertEqual(text, PostViewsTests.post.text)
        self.assertEqual(image, PostViewsTests.post.image)
        self.assertEqual(group, PostViewsTests.group)
        self.assertEqual(comment, PostViewsTests.comment)

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
        self.post_check(response.context)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list', kwargs={
                    'slug': PostViewsTests.group.slug
                }
            )
        )
        group_profile = response.context['group']
        self.post_check(response.context)
        self.assertEqual(group_profile, PostViewsTests.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={
                    'username': PostViewsTests.post.author
                }
            )
        )
        profile_author = response.context['author']
        self.post_check(response.context)
        self.assertEqual(profile_author, PostViewsTests.user)

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
        self.assertEqual(post_detail_context, PostViewsTests.post)
        self.post_check(response.context)
        self.assertIsInstance(response.context.get('form'), CommentForm)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit', kwargs={
                    'post_id': PostViewsTests.post.pk
                }
            )
        )

        self.assertEqual(response.context['post'].id, PostViewsTests.post.id)
        self.assertEqual(
            str(response.context['post']),
            PostViewsTests.post.text
        )
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get('is_edit'), True)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

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
        self.authorized_client.post(reverse('posts:profile_follow', kwargs={
            'username': new_author.username
        }))
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=PostViewsTests.user, author=new_author
            ).exists()
        )

    def test_unfollow(self):
        """Тест отписки"""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='newauthor')
        self.authorized_client.post(reverse('posts:profile_follow', kwargs={
            'username': new_author.username
        }))
        self.authorized_client.post(reverse('posts:profile_unfollow', kwargs={
            'username': new_author.username
        }))
        self.assertEqual(Follow.objects.count(), count_follow)
        self.assertFalse(
            Follow.objects.filter(
                user=PostViewsTests.user, author=new_author
            ).exists()
        )

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


class PaginatorViewsTest(TestCase):
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
            text='Тестовый пост',
            group=cls.group,
        )
        for i in range(1, 13):
            Post.objects.create(
                author=PaginatorViewsTest.post.author,
                text='Тест' + str(i),
                group=PaginatorViewsTest.group,
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_paginator(self):
        cache.clear()
        pages = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list', kwargs={
                    'slug': PaginatorViewsTest.group.slug
                }
            ),
            'profile': reverse(
                'posts:profile', kwargs={
                    'username': PaginatorViewsTest.post.author
                }
            )
        }

        for page_name, page in pages.items():
            with self.subTest(page_name=page_name):
                response_page_1 = self.authorized_client.get(page)
                self.assertEqual(
                    len(response_page_1.context['page_obj']), NUMBER_OF_POSTS
                )

    def test_second_page_paginator(self):
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
