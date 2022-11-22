from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginator_get_page
from .constants import NUMBER_OF_POSTS


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница"""
    posts = Post.objects.select_related(
        'group', 'author'
    ).all()
    page_obj = paginator_get_page(posts, request)
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница группы"""
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).select_related('author').all()
    page_obj = paginator_get_page(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница пользователя"""
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(author=author).exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница информации о посте"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Страница создания поста"""
    form = PostForm(request.POST or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect('posts:profile', post.author)

    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница редактирования поста"""
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()

        return redirect('posts:post_detail', post_id)

    return render(request, 'posts/post_create.html', {
        'form': form, 'is_edit': True, 'post': post
    })


@login_required
def add_comment(request, post_id):
    """Комментирование поста"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница с постами авторов, на которых подписан пользователь"""
    follower_user = request.user
    following_authors = Follow.objects.filter(
        user=follower_user).values('author')
    posts = Post.objects.filter(author__in=following_authors)
    page_obj = paginator_get_page(posts, request)
    context = {
        'page_obj': page_obj,
        'following_users': following_authors
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.create(user=user, author=author)
        return redirect('posts:profile', username)
    return redirect("posts:posts_index")


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if Follow.objects.filter(user=user, author=author).exists():
        Follow.objects.filter(user=user, author=author).delete()
    return redirect("posts:profile", username)
