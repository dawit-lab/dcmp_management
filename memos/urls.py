from django.urls import path
from . import views

urlpatterns = [
    path('', views.memo_list, name='memo-list'),
    path('dashboard/', views.dashboard_memo, name='memo-dashboard'),
    path('create/', views.memo_create, name='memo-create'),
    path('<int:pk>/', views.memo_detail, name='memo-detail'),
    path('<int:pk>/edit/', views.memo_edit, name='memo-edit'),
    path('<int:pk>/delete/', views.memo_delete, name='memo-delete'),
    path('<int:pk>/complete/', views.memo_complete, name='memo-complete'),
    path('<int:pk>/status-change/', views.memo_status_change, name='memo-status-change'),
    
    # New workflow URLs
    path('<int:pk>/dispatch/', views.memo_dispatch, name='memo-dispatch'),
    path('<int:pk>/register/', views.memo_register, name='memo-register'),
    path('<int:pk>/upload-response/', views.memo_upload_response, name='memo-upload-response'),
    path('<int:pk>/complete-workflow/', views.memo_complete_workflow, name='memo-complete-workflow'),
    path('<int:pk>/status-ajax/', views.get_memo_status_ajax, name='memo-status-ajax'),

    # File upload and management URLs
    path('upload/incoming/', views.memo_upload_incoming, name='memo-upload-incoming'),
    path('upload/outgoing/', views.memo_upload_outgoing, name='memo-upload-outgoing'),
    path('bulk-upload/', views.memo_bulk_upload_incoming, name='memo-bulk-upload'),
    path('<int:pk>/view-file/', views.memo_view_file, name='memo-view-file'),
    path('<int:pk>/download-file/', views.memo_download_file, name='memo-download-file'),

    path('setup/', views.memo_setup, name='memo-setup'),

    path('api/create-memo-type/', views.create_memo_type_ajax, name='create-memo-type-ajax'),
    path('api/create-category/', views.create_category_ajax, name='create-category-ajax'),
    path('api/create-department/', views.create_department_ajax, name='create-department-ajax'),
]



# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.memo_list, name='memo-list'),
#     path('dashboard/', views.dashboard_memo, name='memo-dashboard'),
#     path('create/', views.memo_create, name='memo-create'),
#     path('<int:pk>/', views.memo_detail, name='memo-detail'),
#     path('<int:pk>/edit/', views.memo_edit, name='memo-edit'),
#     path('<int:pk>/delete/', views.memo_delete, name='memo-delete'),
#     path('<int:pk>/complete/', views.memo_complete, name='memo-complete'),
#     path('<int:pk>/status-change/', views.memo_status_change, name='memo-status-change'),
# ]