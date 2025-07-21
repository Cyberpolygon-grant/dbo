from django.shortcuts import render

def home(request):
    return render(request, 'index.html')

def accounts(request):
    return render(request, 'accounts.html')

def transfers(request):
    return render(request, 'transfers.html')

def history(request):
    return render(request, 'history.html')

def settings(request):
    return render(request, 'settings.html')
