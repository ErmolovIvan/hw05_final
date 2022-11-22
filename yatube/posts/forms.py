from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма постов"""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """Форма комментариев"""
    class Meta:
        model = Comment
        fields = ('text',)
