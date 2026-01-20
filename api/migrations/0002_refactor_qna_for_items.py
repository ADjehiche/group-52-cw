# Generated manually for Q&A refactoring

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        # Remove old fields from Question
        migrations.RemoveField(
            model_name='question',
            name='title',
        ),
        migrations.RemoveField(
            model_name='question',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='question',
            name='likes',
        ),
        
        # Add item FK to Question
        migrations.AddField(
            model_name='question',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='api.item', null=True, blank=True),
            preserve_default=False,
        ),
        
        # Remove old fields from Answer
        migrations.RemoveField(
            model_name='answer',
            name='author',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='votes',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='is_accepted',
        ),
        
        # Change Answer.question to OneToOneField
        migrations.AlterField(
            model_name='answer',
            name='question',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='answer', to='api.question'),
        ),
    ]
