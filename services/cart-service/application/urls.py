from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartView.as_view(), name='cart_list'),
    path('add/', views.CartAddView.as_view(), name='cart_add'),
    path('<uuid:item_id>/update/', views.CartUpdateView.as_view(), name='cart_update'),
    path('<uuid:item_id>/remove/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('clear/', views.CartClearView.as_view(), name='cart_clear'),
]
