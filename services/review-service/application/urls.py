from django.urls import path
from . import views

urlpatterns = [
    path('', views.ReviewListView.as_view(), name='review_list'),
    path('create/', views.ReviewCreateView.as_view(), name='review_create'),
    path('<uuid:review_id>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('product/<uuid:product_id>/stats/', views.ProductReviewStatsView.as_view(), name='product_review_stats'),
]
