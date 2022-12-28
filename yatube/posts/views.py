from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import (ListView,
                                  DetailView,
                                  CreateView,
                                  UpdateView,
                                  DeleteView,
                                  )

from .models import Group, Post, User, Follow, Comment
from .forms import CommentForm

POST_DISPLAY = 10


@method_decorator(cache_page(1 * 20, key_prefix='index_page'), name='dispatch')
class IndexView(ListView):
    template_name = 'posts/index.html'
    queryset = Post.objects.select_related('author', 'group')
    paginate_by = POST_DISPLAY


class GroupPostsView(ListView):
    template_name = 'posts/group_list.html'
    paginate_by = POST_DISPLAY

    def get_queryset(self):
        self.group = get_object_or_404(Group, slug=self.kwargs['slug'])
        return self.group.posts.select_related('author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        return context


class ProfileView(ListView):
    template_name = 'posts/profile.html'
    paginate_by = POST_DISPLAY

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        return self.author.posts.select_related('group')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_author'] = True
        context['author'] = self.author
        context['following'] = Follow.objects.filter(user=self.request.user.id,
                                                     author=self.author.id,
                                                     ).exists()
        return context


class PostDetailView(DetailView):
    model = Post
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'
    template_name = 'posts/post_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ('text', 'group', 'image')
    template_name = 'posts/create_post.html'

    def get_success_url(self):
        return reverse('posts:profile', args=[self.request.user])

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostEditView(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ('text', 'group', 'image')
    template_name = 'posts/create_post.html'
    pk_url_kwarg = 'post_id'

    def get(self, *args, **kwargs):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        if self.request.user != post.author:
            return redirect('posts:post_detail', self.kwargs['post_id'])
        return super().get(self, *args, **kwargs)

    def get_success_url(self):
        return reverse('posts:post_detail', args=[self.kwargs['post_id']])

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ('text',)

    def get(self, request, *args, **kwargs):
        return redirect('posts:post_detail', post_id=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse('posts:post_detail', args=[self.kwargs['post_id']])

    def form_valid(self, form):
        form.instance.post = get_object_or_404(Post, id=self.kwargs['post_id'])
        form.instance.author = self.request.user
        return super().form_valid(form)


class FollowIndexView(LoginRequiredMixin, ListView):
    template_name = 'posts/follow.html'
    paginate_by = POST_DISPLAY

    def get_queryset(self):
        return (Post.objects.select_related('author', 'group')
                .filter(author__following__user=self.request.user))


class ProfileFollowView(LoginRequiredMixin, CreateView):
    model = Follow
    fields = ()

    # def get_form_kwargs(self):
    #     """Подготавить данные для формы модели Follow, вместо отсутствующих."""
    #     kwargs = super().get_form_kwargs()
    #     kwargs['data'] = {}
    #     return kwargs
    #
    # def get_success_url(self):
    #     return reverse('posts:profile', args=[self.kwargs['username']])
    #
    # def form_valid(self, form):
    #     form.instance.user = self.request.user
    #     form.instance.author = get_object_or_404(
    #         User, username=self.kwargs['username'])
    #     return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs['username'])
        user = self.request.user
        follow = Follow.objects.filter(
            user=user,
            author=author,
        ).exists()
        if follow:
            return redirect('posts:profile', username=self.kwargs['username'])
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs['username'])
        user = self.request.user
        if author != user:
            Follow.objects.create(
                user=user,
                author=author,
            )
        return redirect('posts:profile', username=self.kwargs['username'])


class ProfileUnfollowView(LoginRequiredMixin, DeleteView):
    model = Follow

    def get_success_url(self):
        return reverse('posts:profile', args=[self.kwargs['username']])

    def get_object(self, queryset=None):
        author = get_object_or_404(User, username=self.kwargs['username'])
        return get_object_or_404(Follow,
                                 user=self.request.user,
                                 author=author,
                                 )

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
