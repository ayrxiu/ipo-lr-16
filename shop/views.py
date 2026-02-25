from django.http import HttpResponse

def home(request):
    return HttpResponse("Рыболовный магазин. Главная страница. <a href='/about/'>Об авторке</a> | <a href='/info/'>О магазине</a>")

def about(request):
    return HttpResponse("Якубец Дарья из группы 89TP")

def info(request):
    return HttpResponse("Тема лабы: Создание и базовая настройка приложений Django.")