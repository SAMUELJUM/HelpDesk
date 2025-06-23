from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import KnowledgeBaseArticle, ArticleCategory
from .forms import ArticleForm, RatingForm
from .models import KnowledgeBaseArticle

@login_required
def article_list(request):
    articles = KnowledgeBaseArticle.objects.all().order_by('-created_at')
    return render(request, 'knowledgebase/article_list.html', {'articles': articles})

@login_required
def category_list(request):
    categories = ArticleCategory.objects.all()
    return render(request, 'knowledgebase/category_list.html', {'categories': categories})

@login_required
def article_detail(request, pk):
    article = get_object_or_404(KnowledgeBaseArticle, pk=pk)
    return render(request, 'knowledgebase/article_detail.html', {'article': article})

@login_required
def create_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            messages.success(request, 'Article created successfully!')
            return redirect('article_detail', pk=article.pk)
    else:
        form = ArticleForm()
    return render(request, 'knowledgebase/article_form.html', {'form': form})

@login_required
def edit_article(request, pk):
    article = get_object_or_404(KnowledgeBaseArticle, pk=pk)
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article updated successfully!')
            return redirect('article_detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(request, 'knowledgebase/article_form.html', {'form': form})

@login_required
def rate_article(request, pk):
    article = get_object_or_404(KnowledgeBaseArticle, pk=pk)
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.article = article
            rating.user = request.user
            rating.save()
            messages.success(request, 'Thank you for your rating!')
            return redirect('article_detail', pk=article.pk)
    else:
        form = RatingForm()
    return render(request, 'knowledgebase/rating_form.html', {'form': form, 'article': article})


@login_required
def delete_article(request, pk):
    article = get_object_or_404(KnowledgeBaseArticle, pk=pk)

    if request.user != article.author and not request.user.is_superuser:
        return redirect('knowledgebase:article_list')

    if request.method == 'POST':
        article.delete()
        return redirect('knowledgebase:article_list')

    return render(request, 'knowledgebase/article_confirm_delete.html', {'article': article})