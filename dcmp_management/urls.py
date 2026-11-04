"""
URL configuration for dcmp_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from personnel import views as personnel_views
#from personnel import views  # Importing views to resolve the undefined error

urlpatterns = [
    #path('', include('personnel.urls')),
    #path('api/', include('personnel.urls')),      # API endpoints 
    path('admin/', admin.site.urls),
    #path('', include('personnel.urls')),
    path('memos/', include('memos.urls')),  
    #path('', TemplateView.as_view(template_name='base.html'), name='home'),
    
    # ---- Auth & self-service (root) ----
    path('login/', personnel_views.login_view, name='login'),
    path('logout/', personnel_views.logout_view, name='logout'),
    path('', personnel_views.home_view, name='home'),

    path('interpreter/', personnel_views.interpreter_dashboard, name='interpreter-dashboard'),
    path('translator/', personnel_views.translator_dashboard, name='translator-dashboard'),
    path('coordinator/', personnel_views.coordinator_dashboard, name='coordinator-dashboard'),

    path('my-meeting/upload/<str:doc_type>/',
         personnel_views.my_meeting_upload, name='my-meeting-upload'),

    path('personnel/<int:pk>/demand-availability/',
         personnel_views.demand_availability, name='demand-availability'),

    # ---- API ----
    path('api/', include('personnel.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('__debug__/', include('debug_toolbar.urls')),

    # ---- Availability workflow (root) ----
    path('personnel/<int:pk>/request-availability/',
         personnel_views.request_availability, name='request-availability'),
    path('personnel/<int:pk>/demand-availability/',
         personnel_views.demand_availability, name='demand-availability'),

    path('availability/respond/<str:token>/',
         personnel_views.availability_respond, name='availability-respond'),
    path('availability/<int:pk>/approve/',
         personnel_views.approve_availability, name='approve-availability'),
    path('availability/<int:pk>/decline/',
         personnel_views.decline_availability, name='decline-availability'),

    path('meetings/<int:meeting_id>/availability/',
         personnel_views.meeting_availability_dashboard, name='meeting-availability-dashboard'),
    path('meetings/<int:meeting_id>/availability/bulk/',
         personnel_views.request_availability_bulk, name='request-availability-bulk'),

    path('change-password/', personnel_views.change_password_view, name='change-password'),
    path('contact/', personnel_views.contact_view, name='contact'),

    # ---- Expense web views (HTML pages) ----
    path('expenses/',                        personnel_views.expense_list,        name='expense-list'),
    path('expenses/add/',                    personnel_views.expense_create,      name='expense-add'),
    path('expenses/<int:pk>/',               personnel_views.expense_detail,      name='expense-detail'),
    path('expenses/<int:pk>/edit/',          personnel_views.expense_edit,        name='expense-edit'),
    path('expenses/<int:pk>/delete/',        personnel_views.expense_delete,      name='expense-delete'),
    path('expenses/<int:pk>/toggle-lock/',   personnel_views.expense_toggle_lock, name='expense-toggle-lock'),

    path(
    'personnel/add-from-master/',
    personnel_views.personnel_add_from_master,
    name='personnel-add-from-master',
),

path(
    'api/master-personnel/create/',
    personnel_views.create_master_personnel_ajax,
    name='create-master-personnel-ajax',
),

    # ...existing...
    #path('api/', include('personnel.urls')),   # ← DRF router stays here
    # ...


    # # API URLs
    # path('api/', include('personnel.urls')),
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # # Debug toolbar
    # path('__debug__/', include('debug_toolbar.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns += [
#         path('__debug__/', include('debug_toolbar.urls')),
#     ]