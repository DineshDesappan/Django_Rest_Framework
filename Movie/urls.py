from django.urls import path, include
from .views import StreamPlatformVS, MovieVS, ReviewCreate, ReviewList, ReviewDetail, UserReview
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register('stream', StreamPlatformVS, basename='streamplatform')
router.register('movie', MovieVS, basename='movie')

urlpatterns = [
    path('', include(router.urls)),
    path('movie/<int:pk>/reviews/', ReviewList.as_view(), name='review-list'),
    path('movie/<int:pk>/review/create/', ReviewCreate.as_view(), name='review-create'),
    path('movie/<int:pk>/review/', ReviewDetail.as_view(), name='review-detail'),
    
    path('review', UserReview.as_view(), name='review-user'),
    path('reviewlist/<int:pk>/', ReviewList.as_view(), name='review-list'),
    
]