from django.shortcuts import render

def checkin_page(request):
    return render(request, "attendance_ai/checkin.html")
