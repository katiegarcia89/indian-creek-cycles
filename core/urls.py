from django.urls import path, include
from reservations import views as reservation_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('trails/', views.trails, name='trails'),
    path('contact/', views.contact, name='contact'),
    path('api/weather/', views.weather_api, name='weather_api'),
    path('toggle-trail/<int:trail_id>/', views.toggle_saved_trail, name='toggle_saved_trail'),
    path('trails/<int:id>/', views.trail_detail, name='trail_detail'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path("admin-dashboard/staff/", views.admin_staff, name="admin_staff"),
    path("admin-dashboard/users/", views.admin_users, name="admin_users"),
    path("admin-dashboard/users/<int:user_id>/edit/", views.admin_edit_user, name="admin_edit_user"),
    path("admin-dashboard/users/<int:user_id>/delete/", views.delete_user, name="delete_user"),

    path("admin-dashboard/promos/", views.admin_promos, name="admin_promos"),
    path("admin-dashboard/promos/add/", views.admin_add_promo, name="admin_add_promo"),
    path("admin-dashboard/promos/<int:promo_id>/edit/", views.admin_edit_promo, name="admin_edit_promo"),
    path("admin-dashboard/promos/<int:promo_id>/toggle/", views.toggle_promo_status, name="toggle_promo_status"),
    path("admin-dashboard/promos/<int:promo_id>/delete/", views.delete_promo, name="delete_promo"),

    path("admin-dashboard/bikes/", views.admin_bikes, name="admin_bikes"),
    path("admin-dashboard/bikes/<int:bike_id>/toggle-availability/", views.toggle_bike_availability, name="toggle_bike_availability"),
    path("admin-dashboard/bikes/<int:bike_id>/toggle-maintenance/", views.toggle_bike_maintenance, name="toggle_bike_maintenance"),

    path("admin-dashboard/accessories/", views.admin_accessories, name="admin_accessories"),
    path("admin-dashboard/accessories/add/", views.admin_add_accessory, name="admin_add_accessory"),
    path("admin-dashboard/accessories/<int:accessory_id>/edit/", views.admin_edit_accessory, name="admin_edit_accessory"),
    path("admin-dashboard/accessories/<int:accessory_id>/stock/", views.update_accessory_stock, name="update_accessory_stock"),
    path("admin-dashboard/accessories/<int:accessory_id>/delete/", views.delete_accessory, name="delete_accessory"),
    path("admin-dashboard/accessories/<int:accessory_id>/toggle-availability/", views.toggle_accessory_availability, name="toggle_accessory_availability"),

    path("admin-dashboard/reservations/", views.admin_reservations, name="admin_reservations"),
    path("admin-dashboard/reservations/<int:reservation_id>/status/<str:new_status>/", views.update_reservation_status, name="update_reservation_status"),

    path("admin-dashboard/reviews/", views.admin_reviews, name="admin_reviews"),
    path("admin-dashboard/reviews/<int:review_id>/approve/", views.approve_review, name="approve_review"),
    path("admin-dashboard/reviews/<int:review_id>/unapprove/", views.unapprove_review, name="unapprove_review"),

    path("admin-dashboard/payments/", views.admin_payments, name="admin_payments"),
    path("admin-dashboard/payments/<int:payment_id>/refund/", views.refund_payment, name="refund_payment"),
    path("admin-dashboard/payments/<int:payment_id>/void/", views.void_payment, name="void_payment"),

    path("admin-dashboard/signed-waivers/", views.admin_waivers, name="signed_waivers"),
    
    path('admin-dashboard/send-reminders/', reservation_views.send_daily_reminders, name='send_reminders'),
]                         
