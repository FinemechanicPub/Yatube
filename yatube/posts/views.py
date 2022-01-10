from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, Follow, User
from .services import get_posts_page


def index(request: HttpRequest):
    """Представление главной страницы."""
    return render(request, 'posts/index.html', {
        'page_obj': get_posts_page(request, Post.objects.all()),
        'index': True
    })


def group_posts(request: HttpRequest, slug: str):
    """Представление группы."""
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': get_posts_page(request, group.posts.all())
    })


def profile(request: HttpRequest, username: str):
    """Представление страницы пользователя."""
    author = get_object_or_404(User, username=username)
    user = request.user
    return render(request, 'posts/profile.html', {
        'author': author,
        'following': (
            user.is_authenticated
            and user.follower.filter(author=author).exists()
        ),
        'page_obj': get_posts_page(request, author.posts.all())
    })


def post_detail(request: HttpRequest, post_id: int):
    """Представление для одной публикации."""
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': post.comments.all(),
        'form': CommentForm(request.POST)
    })


@login_required
def post_create(request: HttpRequest):
    """Представление для добавления новой публикации."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user  # @login_required
    post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request: HttpRequest, post_id: int):
    """Представление для редактирования существующей записи."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form,
            'is_edit': True
        })
    form.save()
    return redirect('posts:post_detail', post.pk)


@login_required
def add_comment(request: HttpRequest, post_id: int):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post.pk)


@login_required
def follow_index(request: HttpRequest):
    return render(request, 'posts/follow.html', {
        'page_obj': get_posts_page(
            request, Post.objects.filter(author__following__user=request.user)
        ),
        'follow': True
    })


@login_required
def profile_follow(request: HttpRequest, username: str):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect(request.META.get('HTTP_REFERER', 'posts:follow_index'))


@login_required
def profile_unfollow(request: HttpRequest, username: str):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect(request.META.get('HTTP_REFERER', 'posts:follow_index'))
