from django.http.request import HttpRequest
from django.shortcuts import render


def page_not_found(request: HttpRequest, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_error(request: HttpRequest):
    return render(request, 'core/500.html', {'path': request.path}, status=500)


def permission_denied_view(request: HttpRequest, exception):
    return render(request, 'core/403.html', {'path': request.path}, status=403)
