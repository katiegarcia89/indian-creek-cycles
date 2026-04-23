from django.urls import path
from . import views
from reservations import views as reservation_views  

urlpatterns = [
    path('check-availability/', views.check_availability, name='check_availability'),
    path('create/<slug:bike_slug>/', views.create_reservation, name='create_reservation'),
    path('waiver/<int:reservation_id>/', views.waiver, name='waiver'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('detail/<int:pk>/', views.reservation_detail, name='reservation_detail'),
    path('cancel/<int:pk>/', views.cancel_reservation, name='cancel_reservation'),
    path('confirmation/<int:pk>/', views.reservation_confirmation, name='reservation_confirmation'),
    path('reservation/<int:pk>/unlock/', views.unlock_bike, name='unlock_bike'),
    path('dashboard/send-reminders/', reservation_views.send_daily_reminders, name='send_reminders'),
    path('reservation/<int:reservation_id>/process-unlock/', views.process_unlock, name='process_unlock'),
    path('reservation/<int:reservation_id>/process-return/', views.process_return, name='process_return'),
    path('reservation/<int:reservation_id>/confirm-location/', views.confirm_pickup_location, name='confirm_pickup_location'),
    path('find-next/', views.find_next_reservation, name='find_next_reservation'),
    path('help/', views.help_page, name='help'),
]
