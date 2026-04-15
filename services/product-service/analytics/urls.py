from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.TrackProductView.as_view(), name='track_view'),
    path('search/', views.TrackSearchView.as_view(), name='track_search'),
    path('event/', views.TrackClickEventView.as_view(), name='track_event'),
    path('behavior/', views.BehaviorDataView.as_view(), name='behavior_data'),
]
