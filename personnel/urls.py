# personnel/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'personnel', views.PersonnelViewSet, basename='personnel')
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'meetings', views.MeetingViewSet, basename='meeting')
router.register(r'communications', views.CommunicationViewSet, basename='communication')
router.register(r'expenses', views.PersonnelExpenseViewSet, basename='expense')

urlpatterns = [
    #path('', views.home, name='home'),
    #path('', include(router.urls)),
    path('personnel/add/', views.personnel_create, name='personnel-add'),
    path('api/meetings/create/', views.create_meeting_ajax, name='create-meeting-ajax'),
    path('meeting/create/', views.meeting_create, name='meeting-create'),
    path('personnel/add/<int:meeting_id>/', views.personnel_create, name='personnel-add-with-meeting'),   
    # API Routes
    path('', include(router.urls)),
    
    # Custom API Endpoints
    path('personnel/upload-bulk/', views.bulk_upload_personnel, name='bulk-upload'),
    path('personnel/<int:pk>/documents/', views.get_personnel_documents, name='personnel-documents'),
    path('personnel/<int:pk>/send-reminder/', views.send_document_reminder, name='send-reminder'),
    path('personnel/<int:pk>/send-to-finance/', views.send_to_finance, name='send-to-finance'),
    path(
        'personnel/<int:person_id>/calculate-payment-and-redirect/',
        views.calculate_payment_and_redirect,
        name='personnel-calculate-payment-and-redirect'
    ),
    path('personnel/<int:pk>/calculate-payment/', views.calculate_payment, name='calculate-payment'),
    path('documents/upload/', views.upload_document, name='upload-document'),
    path('documents/<int:pk>/download/', views.download_document, name='download-document'),
    path('payments/generate-report/', views.generate_payment_report, name='payment-report'),
    
    # Web Views (for dashboard)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('personnel-list/', views.personnel_list, name='personnel-list'),
    path('personnel/<int:pk>/detail/', views.personnel_detail, name='personnel-detail'),
    path('personnel/<int:pk>/upload-document/', views.upload_document_view, name='upload-document-view'),
    path('payment/<int:pk>/detail/', views.payment_detail, name='payment-detail'),

    path('personnel/<int:pk>/detail/', views.personnel_detail, name='personnel-detail'),
    path('document/upload/<int:personnel_id>/', views.upload_document, name='upload-document'),
    path('document/replace/<int:doc_id>/', views.replace_document, name='replace-document'),
    path('document/download/<int:doc_id>/', views.download_document, name='download-document'),
    path('document/view/<int:doc_id>/', views.view_document, name='view-document'),
    #path('api/', include(router.urls)),
    path('dashboard-table/', views.personnel_dashboard, name='personnel-dashboard-table'),
    path('payment/<int:pk>/', views.payment_detail_view, name='payment-detail'),

    path('personnel/<int:pk>/edit/', views.personnel_edit, name='personnel-edit'),
    path('personnel/<int:pk>/delete/', views.personnel_delete, name='personnel-delete'),

    path('payment-settings/', views.payment_settings_view, name='payment-settings'),

    path('debug/', views.debug_view, name='debug'),

    path('personnel/<int:pk>/merge/', views.merge_documents_view, name='merge-documents'),
    path('personnel/<int:pk>/merge/download/<str:format>/', views.merge_documents_download, name='merge-documents-download'),
    path('api/personnel/<int:pk>/merge/', views.merge_documents_api, name='merge-documents-api'),
    path('api/personnel/<int:pk>/merge-status/', views.merge_documents_status_api, name='merge-documents-status-api'),
    path('merge-history/', views.merge_history_view, name='merge-history'),

    

    

    # Expense CRUD (web)
    # path('expenses/',                          views.expense_list,        name='expense-list'),
    # path('expenses/add/',                      views.expense_create,      name='expense-add'),
    # path('expenses/<int:pk>/',                 views.expense_detail,      name='expense-detail'),
    # path('expenses/<int:pk>/edit/',            views.expense_edit,        name='expense-edit'),
    # path('expenses/<int:pk>/delete/',          views.expense_delete,      name='expense-delete'),
    # path('expenses/<int:pk>/toggle-lock/',     views.expense_toggle_lock, name='expense-toggle-lock'),


    #     # Auth & self-service
    # path('login/', views.login_view, name='login'),
    # path('logout/', views.logout_view, name='logout'),
    # path('', views.home_view, name='home'),

    # path('interpreter/', views.interpreter_dashboard, name='interpreter-dashboard'),
    # path('translator/', views.translator_dashboard, name='translator-dashboard'),
    # path('coordinator/', views.coordinator-dashboard, name='coordinator-dashboard'),

    # path('my-meeting/upload/<str:doc_type>/', views.my_meeting_upload, name='my-meeting-upload'),

    # # Admin actions
    # path('personnel/<int:pk>/demand-availability/', views.demand_availability, name='demand-availability'),
]