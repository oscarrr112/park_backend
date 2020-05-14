from django.views import View
from django.http import JsonResponse


class LogView(View):
    def get(self, request):
        log = request.GET.get('log')
        print(log)
        return JsonResponse(data={'data': 'data'}, safe=False)
