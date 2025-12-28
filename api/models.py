from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass

class PageView(models.Model):
    count = models.IntegerField(default=0)

    def __str__(self):
        return f"Page view count: {self.count}"


class Question(models.Model):
    title: str = models.CharField(max_length=200)
    content: str = models.TextField()
    author: User = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)
    likes: int = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Answer(models.Model):
    question: Question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    content: str = models.TextField()
    author: User = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)
    votes: int = models.IntegerField(default=0)
    is_accepted: bool = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_accepted', '-votes', '-created_at']

    def __str__(self):
        return f"Answer to '{self.question.title}' by {self.author.username}" 
    