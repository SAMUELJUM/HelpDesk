from django.shortcuts import render

def dashboard_view(request):
    return render(request, 'dashboard.html')  # You need to create templates/home.html
