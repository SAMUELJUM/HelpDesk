from django.shortcuts import redirect
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'ADMIN':
            return view_func(request, *args, **kwargs)
        return redirect('users:login')
    return wrapper

def technician_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'TECH':
            return view_func(request, *args, **kwargs)
        return redirect('users:login')
    return wrapper

def employee_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'EMP':
            return view_func(request, *args, **kwargs)
        return redirect('users:login')
    return wrapper
