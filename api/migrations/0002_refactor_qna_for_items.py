# Generated manually for Q&A refactoring

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def deduplicate_answers(apps, schema_editor):
    """
    Remove duplicate answers for each question.
    Keep the accepted answer if present, otherwise keep the most recent answer.
    """
    Answer = apps.get_model('api', 'Answer')
    Question = apps.get_model('api', 'Question')
    
    for question in Question.objects.all():
        answers = Answer.objects.filter(question=question).order_by('-is_accepted', '-created_at')
        if answers.count() > 1:
            # Keep the first answer (accepted or most recent)
            to_keep = answers.first()
            # Delete all others
            Answer.objects.filter(question=question).exclude(pk=to_keep.pk).delete()


def reverse_deduplicate_answers(apps, schema_editor):
    """
    No-op: We cannot restore deleted duplicate answers.
    """
    pass


def backfill_question_item(apps, schema_editor):
    """
    Handle existing Questions that don't have an item assigned.
    Since we can't automatically determine which item a question belongs to,
    we'll delete orphaned questions (questions without an item).
    
    In production, you might want to:
    - Manually assign items to questions before running this migration
    - Or keep questions but set a default item
    """
    Question = apps.get_model('api', 'Question')
    
    # Delete questions that don't have an item (null item)
    orphaned_count = Question.objects.filter(item__isnull=True).count()
    if orphaned_count > 0:
        Question.objects.filter(item__isnull=True).delete()
        print(f"Deleted {orphaned_count} orphaned questions without an item.")


def reverse_backfill_question_item(apps, schema_editor):
    """
    No-op: We cannot restore deleted questions.
    """
    pass


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
        
        # Add item FK to Question (nullable first)
        migrations.AddField(
            model_name='question',
            name='item',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='questions',
                to='api.item',
                null=True,
                blank=True
            ),
            preserve_default=False,
        ),
        
        # Backfill or delete questions without items
        migrations.RunPython(
            backfill_question_item,
            reverse_backfill_question_item,
        ),
        
        # Make item field non-nullable
        migrations.AlterField(
            model_name='question',
            name='item',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='questions',
                to='api.item'
            ),
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
        
        # Deduplicate answers BEFORE changing to OneToOneField
        migrations.RunPython(
            deduplicate_answers,
            reverse_deduplicate_answers,
        ),
        
        # Change Answer.question to OneToOneField
        migrations.AlterField(
            model_name='answer',
            name='question',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='answer',
                to='api.question'
            ),
        ),
    ]
