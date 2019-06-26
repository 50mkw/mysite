from django.shortcuts import render
from django.views import generic
from .models import Flow

# Create your views here.

class IndexView(generic.ListView):
    template_name = 'recml/index.html'
    context_object_name = 'flow_full_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Flow.objects.all()