from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegisterForm, SubjectForm, NoteForm, TaskForm, TimetableForm
from .models import Subject, Note, Task, TimetableEntry


def _form_page(request, form, title):
    return render(request, 'study/form.html', {'form': form, 'title': title})


def _confirm_delete(request, obj, back, label):
    if request.method == 'POST':
        obj.delete()
        messages.success(request, f'{label} deleted.')
        return redirect(back)
    return render(request, 'study/confirm_delete.html', {'object': obj, 'back': back})


# ---------- Auth ----------
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'study/register.html', {'form': form})


# ---------- Dashboard ----------
@login_required
def dashboard(request):
    user = request.user
    today = timezone.localdate()

    tasks = Task.objects.filter(user=user)
    total = tasks.count()
    completed = tasks.filter(status='completed').count()
    open_tasks = tasks.exclude(status='completed')
    progress = round(completed * 100 / total) if total else 0

    planned = {}
    for slot in TimetableEntry.objects.filter(user=user):
        planned[slot.subject_id] = planned.get(slot.subject_id, 0) + slot.duration_hours()

    subjects = Subject.objects.filter(user=user)
    subject_progress = []
    for s in subjects:
        hours = round(planned.get(s.id, 0), 1)
        percent = min(100, round(hours * 100 / s.target_hours)) if s.target_hours else 0
        subject_progress.append({'subject': s, 'planned': hours, 'percent': percent})

    context = {
        'subject_count': subjects.count(),
        'pending': total - completed,
        'completed': completed,
        'overdue': open_tasks.filter(due_date__lt=today).count(),
        'progress': progress,
        'upcoming': open_tasks.filter(due_date__gte=today).select_related('subject')[:5],
        'todays_classes': TimetableEntry.objects.filter(user=user, day=today.weekday()).select_related('subject'),
        'subject_progress': subject_progress,
    }
    return render(request, 'study/dashboard.html', context)


# ---------- Subjects & notes ----------
@login_required
def subject_list(request):
    subjects = Subject.objects.filter(user=request.user)
    return render(request, 'study/subject_list.html', {'subjects': subjects})


@login_required
def subject_add(request):
    form = SubjectForm(request.POST or None)
    if form.is_valid():
        subject = form.save(commit=False)
        subject.user = request.user
        subject.save()
        messages.success(request, 'Subject added.')
        return redirect('subject_list')
    return _form_page(request, form, 'Add subject')


@login_required
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk, user=request.user)
    form = SubjectForm(request.POST or None, instance=subject)
    if form.is_valid():
        form.save()
        messages.success(request, 'Subject updated.')
        return redirect('subject_list')
    return _form_page(request, form, 'Edit subject')


@login_required
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk, user=request.user)
    return _confirm_delete(request, subject, 'subject_list', 'Subject')


@login_required
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk, user=request.user)
    form = NoteForm(request.POST or None)
    if form.is_valid():
        note = form.save(commit=False)
        note.subject = subject
        note.save()
        messages.success(request, 'Note added.')
        return redirect('subject_detail', pk=pk)
    return render(request, 'study/subject_detail.html', {
        'subject': subject,
        'form': form,
        'notes': subject.notes.all(),
        'tasks': subject.tasks.all(),
    })


@login_required
@require_POST
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, subject__user=request.user)
    subject_id = note.subject_id
    note.delete()
    messages.success(request, 'Note deleted.')
    return redirect('subject_detail', pk=subject_id)


# ---------- Tasks ----------
@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user).select_related('subject')
    current = request.GET.get('status', '')
    if current in dict(Task.STATUS_CHOICES):
        tasks = tasks.filter(status=current)
    return render(request, 'study/task_list.html', {'tasks': tasks, 'current': current})


@login_required
def task_add(request):
    if not Subject.objects.filter(user=request.user).exists():
        messages.info(request, 'Add a subject first, then you can create tasks.')
        return redirect('subject_add')
    form = TaskForm(request.POST or None, user=request.user)
    if form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        messages.success(request, 'Task added.')
        return redirect('task_list')
    return _form_page(request, form, 'Add task')


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    form = TaskForm(request.POST or None, instance=task, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Task updated.')
        return redirect('task_list')
    return _form_page(request, form, 'Edit task')


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    return _confirm_delete(request, task, 'task_list', 'Task')


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.status = 'pending' if task.status == 'completed' else 'completed'
    task.save()
    return redirect('task_list')


# ---------- Timetable ----------
@login_required
def timetable(request):
    entries = TimetableEntry.objects.filter(user=request.user).select_related('subject')
    days = [(label, [e for e in entries if e.day == value]) for value, label in TimetableEntry.DAY_CHOICES]
    return render(request, 'study/timetable.html', {'days': days})


@login_required
def timetable_add(request):
    if not Subject.objects.filter(user=request.user).exists():
        messages.info(request, 'Add a subject first, then you can build your timetable.')
        return redirect('subject_add')
    form = TimetableForm(request.POST or None, user=request.user)
    if form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.save()
        messages.success(request, 'Timetable slot added.')
        return redirect('timetable')
    return _form_page(request, form, 'Add timetable slot')


@login_required
def timetable_delete(request, pk):
    entry = get_object_or_404(TimetableEntry, pk=pk, user=request.user)
    return _confirm_delete(request, entry, 'timetable', 'Timetable slot')