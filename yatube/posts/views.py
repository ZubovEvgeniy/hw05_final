from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from posts.helper import paginator


def index(request):
    post_list = Post.objects.all()
    # В словаре context отправляем информацию в шаблон
    return render(
        request,
        'posts/index.html',
        {'page_obj': paginator(request, post_list)},
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    context = {
        'group': group,
        'page_obj': paginator(request, posts),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()
    context = {
        'page_obj': paginator(request, post_list),
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comment = post.comments.filter(post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'comment': comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=str(request.user))
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    return render(
        request,
        'posts/follow.html',
        {'page_obj': paginator(request, post_list)},
    )


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect(
            'posts:profile',
            username=username,
        )
    if Follow.objects.filter(
        user=request.user,
        author=author
    ).exists():
        return redirect(
            'posts:profile',
            username=username,
        )
    Follow.objects.create(user=request.user, author=author)
    return redirect(
        'posts:profile',
        username=username,
    )


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect(
            'posts:profile',
            username=username,
        )
    following = get_object_or_404(Follow, user=request.user, author=author)
    following.delete()
    return redirect(
        'posts:profile',
        username=username,
    )
