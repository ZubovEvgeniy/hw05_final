from xml.etree.ElementTree import Comment
from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        labels = {
            'group': 'Группа',
            'text': 'Текст поста',
            'image': 'Изображение',
        }
        help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
            'image': 'Загрузите изображение',
        }
        fields = ['text', 'group', 'image']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
        fields = ['text']
