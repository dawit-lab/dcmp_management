from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, FileResponse
from django.utils import timezone
from .models import Memo, Department, MemoType, MemoCategory, MemoAction
from .forms import MemoForm, MemoCommentForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Memo, Department, MemoType, MemoCategory, MemoAction, MemoComment
from .forms import MemoForm, MemoCommentForm, ResponseForm, MemoUploadForm

@login_required
def memo_list(request):
    """List all memos with filtering and search"""
    memos = Memo.objects.all().select_related(
        'sender_department', 'receiver_department', 'category', 'memo_type'
    )
    
    # Filters
    direction = request.GET.get('direction')
    if direction:
        memos = memos.filter(direction=direction)
    
    status = request.GET.get('status')
    if status:
        memos = memos.filter(status=status)
    
    category = request.GET.get('category')
    if category:
        memos = memos.filter(category__category_type=category)
    
    priority = request.GET.get('priority')
    if priority:
        memos = memos.filter(priority=priority)
    
    department = request.GET.get('department')
    if department:
        memos = memos.filter(
            Q(sender_department__id=department) |
            Q(receiver_department__id=department)
        )
    
    search = request.GET.get('search')
    if search:
        memos = memos.filter(
            Q(reference_number__icontains=search) |
            Q(subject__icontains=search) |
            Q(content__icontains=search)
        )
    
    # Group memos by status
    grouped_memos = {}
    for memo in memos:
        if memo.status not in grouped_memos:
            grouped_memos[memo.status] = []
        grouped_memos[memo.status].append(memo)
    
    context = {
        'grouped_memos': grouped_memos,
        'total_count': memos.count(),
        'completed_count': memos.filter(is_completed=True).count(),
        'pending_count': memos.filter(is_completed=False).count(),
        'overdue_count': memos.filter(is_completed=False).filter(due_date__lt=timezone.now().date()).count(),
        'memo_categories': MemoCategory.CATEGORY_TYPES,
        'departments': Department.objects.filter(is_active=True),
        'filters': {
            'direction': direction,
            'status': status,
            'category': category,
            'priority': priority,
            'department': department,
            'search': search,
        }
    }
    return render(request, 'memos/memo_list.html', context)

@login_required
# memos/views.py - memo_create and memo_edit

def memo_create(request):
    if request.method == 'POST':
        form = MemoForm(request.POST, request.FILES)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.created_by = request.user
            memo.save()
            messages.success(request, f'Memo "{memo.reference_number}" created successfully!')
            return redirect('memo-detail', pk=memo.id)
    else:
        form = MemoForm()
    
    context = {
        'form': form,
        'title': 'Create New Memo',
        'category_choices': MemoCategory.CATEGORY_TYPES,  # Add this
    }
    return render(request, 'memos/memo_form.html', context)

def memo_edit(request, pk):
    memo = get_object_or_404(Memo, id=pk)
    
    if request.method == 'POST':
        form = MemoForm(request.POST, request.FILES, instance=memo)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.last_updated_by = request.user
            memo.save()
            messages.success(request, f'Memo "{memo.reference_number}" updated successfully!')
            return redirect('memo-detail', pk=memo.id)
    else:
        form = MemoForm(instance=memo)
    
    context = {
        'form': form,
        'memo': memo,
        'title': f'Edit Memo: {memo.reference_number}',
        'category_choices': MemoCategory.CATEGORY_TYPES,  # Add this
    }
    return render(request, 'memos/memo_form.html', context)

@login_required
def memo_detail(request, pk):
    """View memo details"""
    memo = get_object_or_404(Memo, id=pk)
    actions = memo.actions.all()
    comments = memo.comments.all()
    
    if request.method == 'POST':
        form = MemoCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.memo = memo
            comment.created_by = request.user
            comment.save()
            
            # Add action log
            MemoAction.objects.create(
                memo=memo,
                action_type='comment',
                description=f"Comment added by {request.user.username}",
                performed_by=request.user
            )
            
            messages.success(request, 'Comment added successfully!')
            return redirect('memo-detail', pk=memo.id)
    else:
        form = MemoCommentForm()
    
    context = {
        'memo': memo,
        'actions': actions,
        'comments': comments,
        'form': form,
        'status_badge_class': {
            'draft': 'secondary',
            'sent': 'info',
            'received': 'primary',
            'in_progress': 'warning',
            'completed': 'success',
            'rejected': 'danger',
            'archived': 'secondary',
        },
        'priority_badge_class': {
            'low': 'success',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger',
        }
    }
    return render(request, 'memos/memo_detail.html', context)

@login_required
def memo_edit(request, pk):
    """Edit a memo"""
    memo = get_object_or_404(Memo, id=pk)
    
    if request.method == 'POST':
        form = MemoForm(request.POST, request.FILES, instance=memo)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.last_updated_by = request.user
            memo.save()
            
            messages.success(request, f'Memo "{memo.reference_number}" updated successfully!')
            return redirect('memo-detail', pk=memo.id)
    else:
        form = MemoForm(instance=memo)
    
    context = {
        'form': form,
        'memo': memo,
        'title': f'Edit Memo: {memo.reference_number}',
    }
    return render(request, 'memos/memo_form.html', context)

@login_required
def memo_delete(request, pk):
    """Delete a memo"""
    memo = get_object_or_404(Memo, id=pk)
    
    if request.method == 'POST':
        reference = memo.reference_number
        memo.delete()
        messages.success(request, f'Memo "{reference}" deleted successfully!')
        return redirect('memo-list')
    
    context = {
        'memo': memo,
    }
    return render(request, 'memos/memo_confirm_delete.html', context)

@login_required
def memo_complete(request, pk):
    """Mark memo as completed"""
    memo = get_object_or_404(Memo, id=pk)
    
    if request.method == 'POST':
        memo.mark_as_completed()
        messages.success(request, f'Memo "{memo.reference_number}" marked as completed!')
        return redirect('memo-detail', pk=memo.id)
    
    return redirect('memo-detail', pk=memo.id)

@login_required
def memo_status_change(request, pk):
    """Change memo status"""
    memo = get_object_or_404(Memo, id=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Memo.MEMO_STATUS):
            memo.status = new_status
            memo.last_updated_by = request.user
            
            if new_status == 'completed':
                memo.is_completed = True
                memo.completed_date = timezone.now().date()
            
            memo.save()
            
            # Add action log
            MemoAction.objects.create(
                memo=memo,
                action_type='status_changed',
                description=f"Status changed to {memo.get_status_display()} by {request.user.username}",
                performed_by=request.user
            )
            
            messages.success(request, f'Status updated to "{memo.get_status_display()}"')
        else:
            messages.error(request, 'Invalid status selected')
    
    return redirect('memo-detail', pk=memo.id)

@login_required
def dashboard_memo(request):
    """Memo dashboard with statistics"""
    total_memos = Memo.objects.count()
    incoming = Memo.objects.filter(direction='incoming').count()
    outgoing = Memo.objects.filter(direction='outgoing').count()
    pending = Memo.objects.filter(is_completed=False).count()
    completed = Memo.objects.filter(is_completed=True).count()
    overdue = Memo.objects.filter(is_completed=False).filter(due_date__lt=timezone.now().date()).count()
    
    # Recent memos
    recent_memos = Memo.objects.all().order_by('-created_at')[:10]
    
    # Memos by category
    categories = {}
    for category_type, label in MemoCategory.CATEGORY_TYPES:
        count = Memo.objects.filter(category__category_type=category_type).count()
        if count > 0:
            categories[label] = count
    
    context = {
        'total_memos': total_memos,
        'incoming': incoming,
        'outgoing': outgoing,
        'pending': pending,
        'completed': completed,
        'overdue': overdue,
        'recent_memos': recent_memos,
        'categories': categories,
    }
    return render(request, 'memos/memo_dashboard.html', context)

@login_required
def memo_dispatch(request, pk):
    """Dispatch an incoming memo to OIC/HoD"""
    memo = get_object_or_404(Memo, id=pk)
    
    if request.method == 'POST':
        dispatched_to = request.POST.get('dispatched_to')
        notes = request.POST.get('notes', '')
        
        if not dispatched_to:
            messages.error(request, 'Please specify who to dispatch to')
            return redirect('memo-detail', pk=memo.id)
        
        memo.dispatched_to = dispatched_to
        memo.dispatch_date = timezone.now().date()
        memo.status = 'dispatched'
        memo.last_updated_by = request.user
        memo.save()
        
        # Add action log
        MemoAction.objects.create(
            memo=memo,
            action_type='dispatched',
            description=f"Dispatched to {dispatched_to} by {request.user.username}",
            performed_by=request.user,
            metadata={'dispatched_to': dispatched_to, 'notes': notes}
        )
        
        messages.success(request, f'Memo dispatched to {dispatched_to} successfully!')
        return redirect('memo-detail', pk=memo.id)
    
    return redirect('memo-detail', pk=memo.id)

@login_required
def memo_upload_response(request, pk):
    """Upload draft and signed response for a memo"""
    memo = get_object_or_404(Memo, id=pk)
    
    if request.method == 'POST':
        form = ResponseForm(request.POST, request.FILES, instance=memo)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.last_updated_by = request.user
            
            # Update status based on what was uploaded
            if memo.signed_response:
                memo.status = 'response_sent'
                memo.response_date = timezone.now().date()
                memo.is_response_complete = True
                action_type = 'response_sent'
                action_desc = f"Signed response uploaded and sent by {request.user.username}"
            elif memo.draft_response:
                memo.status = 'response_prepared'
                action_type = 'response_drafted'
                action_desc = f"Draft response uploaded by {request.user.username}"
            else:
                messages.error(request, 'Please upload at least a draft or signed response')
                return redirect('memo-detail', pk=memo.id)
            
            memo.save()
            
            # Add action log
            MemoAction.objects.create(
                memo=memo,
                action_type=action_type,
                description=action_desc,
                performed_by=request.user
            )
            
            messages.success(request, 'Response uploaded successfully!')
            return redirect('memo-detail', pk=memo.id)
    else:
        form = ResponseForm(instance=memo)
    
    context = {
        'form': form,
        'memo': memo,
    }
    return render(request, 'memos/upload_response.html', context)

@login_required
def memo_register(request, pk):
    """Register an incoming memo in the registry"""
    memo = get_object_or_404(Memo, id=pk)
    
    if request.method == 'POST':
        registry_number = request.POST.get('registry_number')
        received_from = request.POST.get('received_from')
        
        if registry_number:
            memo.registry_number = registry_number
        if received_from:
            memo.received_from = received_from
        
        memo.status = 'registered'
        memo.received_date = memo.received_date or timezone.now().date()
        memo.last_updated_by = request.user
        memo.save()
        
        # Add action log
        MemoAction.objects.create(
            memo=memo,
            action_type='registered',
            description=f"Memo registered by {request.user.username}",
            performed_by=request.user,
            metadata={'registry_number': memo.registry_number}
        )
        
        messages.success(request, f'Memo registered with number: {memo.registry_number}')
        return redirect('memo-detail', pk=memo.id)
    
    return redirect('memo-detail', pk=memo.id)

@login_required
def memo_complete_workflow(request, pk):
    """Complete the entire memo workflow"""
    memo = get_object_or_404(Memo, id=pk)
    
    if request.method == 'POST':
        notes = request.POST.get('completion_notes', '')
        
        # Check if all required steps are completed
        if memo.direction == 'incoming' and memo.requires_response:
            if not memo.is_response_complete:
                messages.error(request, 'Response must be completed before closing the memo')
                return redirect('memo-detail', pk=memo.id)
        
        memo.mark_as_completed(notes)
        memo.last_updated_by = request.user
        memo.save()
        
        # Add action log
        MemoAction.objects.create(
            memo=memo,
            action_type='completed',
            description=f"Memo workflow completed by {request.user.username}",
            performed_by=request.user,
            metadata={'notes': notes}
        )
        
        messages.success(request, f'Memo "{memo.reference_number}" workflow completed successfully!')
        return redirect('memo-detail', pk=memo.id)
    
    return redirect('memo-detail', pk=memo.id)

@login_required
def get_memo_status_ajax(request, pk):
    """AJAX endpoint to get memo status"""
    memo = get_object_or_404(Memo, id=pk)
    data = {
        'id': memo.id,
        'reference_number': memo.reference_number,
        'status': memo.status,
        'status_display': memo.get_status_display(),
        'is_completed': memo.is_completed,
        'is_overdue': memo.is_overdue(),
        'requires_response': memo.requires_response,
        'is_response_complete': memo.is_response_complete,
        'steps': memo.get_workflow_steps(),
    }
    return JsonResponse(data)

# Add to memos/views.py

@login_required
def memo_upload_incoming(request):
    """Upload and register an incoming memo"""
    if request.method == 'POST':
        form = MemoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.direction = 'incoming'
            memo.status = 'registered'
            memo.created_by = request.user
            memo.uploaded_by = request.user
            memo.upload_date = timezone.now()
            
            # Set file metadata
            if memo.incoming_memo_file:
                memo.file_name = memo.incoming_memo_file.name
                memo.file_size = memo.incoming_memo_file.size
                memo.file_type = memo.incoming_memo_file.content_type
            
            memo.save()
            
            # Generate registry number
            memo.registry_number = f"REG-{timezone.now().strftime('%Y')}-{str(memo.id).zfill(4)}"
            memo.save()
            
            # Add action log
            MemoAction.objects.create(
                memo=memo,
                action_type='registered',
                description=f"Incoming memo uploaded and registered by {request.user.username}",
                performed_by=request.user,
                metadata={'file_name': memo.file_name}
            )
            
            messages.success(request, f'Incoming memo "{memo.reference_number}" uploaded successfully!')
            return redirect('memo-detail', pk=memo.id)
    else:
        form = MemoUploadForm()
    
    context = {
        'form': form,
        'title': 'Upload Incoming Memo',
    }
    return render(request, 'memos/memo_upload_incoming.html', context)

@login_required
def memo_upload_outgoing(request):
    """Upload an outgoing memo"""
    if request.method == 'POST':
        form = MemoForm(request.POST, request.FILES)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.direction = 'outgoing'
            memo.created_by = request.user
            memo.uploaded_by = request.user
            memo.upload_date = timezone.now()
            
            # Set file metadata
            if memo.outgoing_memo_file:
                memo.file_name = memo.outgoing_memo_file.name
                memo.file_size = memo.outgoing_memo_file.size
                memo.file_type = memo.outgoing_memo_file.content_type
            
            memo.save()
            
            # Generate dispatch number
            memo.dispatch_number = f"DSP-{timezone.now().strftime('%Y')}-{str(memo.id).zfill(4)}"
            memo.save()
            
            # Add action log
            MemoAction.objects.create(
                memo=memo,
                action_type='created',
                description=f"Outgoing memo created by {request.user.username}",
                performed_by=request.user
            )
            
            messages.success(request, f'Outgoing memo "{memo.reference_number}" created successfully!')
            return redirect('memo-detail', pk=memo.id)
    else:
        form = MemoForm(initial={'direction': 'outgoing'})
    
    context = {
        'form': form,
        'title': 'Create Outgoing Memo',
    }
    return render(request, 'memos/memo_form.html', context)

@login_required
def memo_view_file(request, pk):
    """View the uploaded incoming memo file"""
    memo = get_object_or_404(Memo, id=pk)
    if memo.incoming_memo_file:
        return FileResponse(
            memo.incoming_memo_file.open('rb'),
            content_type=memo.incoming_memo_file.content_type or 'application/octet-stream',
            as_attachment=False
        )
    messages.error(request, 'No file found for this memo')
    return redirect('memo-detail', pk=memo.id)

@login_required
def memo_download_file(request, pk):
    """Download the uploaded incoming memo file"""
    memo = get_object_or_404(Memo, id=pk)
    if memo.incoming_memo_file:
        return FileResponse(
            memo.incoming_memo_file.open('rb'),
            as_attachment=True,
            filename=memo.incoming_memo_file.name
        )
    messages.error(request, 'No file found for this memo')
    return redirect('memo-detail', pk=memo.id)

@login_required
def memo_bulk_upload_incoming(request):
    """Bulk upload multiple incoming memos"""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES.get('file')
        try:
            # Handle Excel bulk upload
            import pandas as pd
            df = pd.read_excel(file)
            created_count = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    memo = Memo.objects.create(
                        direction='incoming',
                        subject=row.get('Subject', ''),
                        sender_department_id=row.get('Sender Department ID'),
                        receiver_department_id=row.get('Receiver Department ID'),
                        memo_date=row.get('Memo Date', timezone.now().date()),
                        received_date=row.get('Received Date', timezone.now().date()),
                        priority=row.get('Priority', 'medium'),
                        status='registered',
                        created_by=request.user,
                        uploaded_by=request.user,
                        upload_date=timezone.now(),
                    )
                    # Generate registry number
                    memo.registry_number = f"REG-{timezone.now().strftime('%Y')}-{str(memo.id).zfill(4)}"
                    memo.save()
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {_+2}: {str(e)}")
            
            if created_count > 0:
                messages.success(request, f'Successfully imported {created_count} incoming memos')
            if errors:
                messages.warning(request, f'Errors in {len(errors)} rows: {errors[:3]}...' if len(errors) > 3 else ', '.join(errors))
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
        
        return redirect('memo-list')
    
    context = {
        'departments': Department.objects.filter(is_active=True),
    }
    return render(request, 'memos/memo_bulk_upload.html', context)

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Department, MemoType, MemoCategory

@staff_member_required
def memo_setup(request):
    """Setup page to create initial data"""
    if request.method == 'POST':
        # Create Department
        if 'department_name' in request.POST:
            name = request.POST.get('department_name')
            code = request.POST.get('department_code')
            if name and code:
                Department.objects.get_or_create(
                    code=code.upper(),
                    defaults={'name': name, 'is_active': True}
                )
                messages.success(request, f'Department "{name}" created!')
        
        # Create Memo Type
        if 'memo_type_name' in request.POST:
            name = request.POST.get('memo_type_name')
            code = request.POST.get('memo_type_code')
            if name and code:
                MemoType.objects.get_or_create(
                    code=code.upper(),
                    defaults={'name': name}
                )
                messages.success(request, f'Memo Type "{name}" created!')
        
        # Create Memo Category
        if 'category_name' in request.POST:
            name = request.POST.get('category_name')
            category_type = request.POST.get('category_type')
            if name and category_type:
                MemoCategory.objects.get_or_create(
                    category_type=category_type,
                    defaults={'name': name}
                )
                messages.success(request, f'Category "{name}" created!')
        
        return redirect('memo-setup')
    
    context = {
        'departments': Department.objects.filter(is_active=True),
        'memo_types': MemoType.objects.all(),
        'categories': MemoCategory.objects.all(),
        'category_choices': MemoCategory.CATEGORY_TYPES,
    }
    return render(request, 'memos/memo_setup.html', context)

# memos/views.py - Add these views

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@login_required
@csrf_exempt
def create_memo_type_ajax(request):
    """AJAX endpoint to create a new memo type"""
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        code = data.get('code', '').strip().upper()
        
        if not name or not code:
            return JsonResponse({'error': 'Name and code are required'}, status=400)
        
        # Check if code already exists
        if MemoType.objects.filter(code=code).exists():
            return JsonResponse({'error': f'Memo type with code "{code}" already exists'}, status=400)
        
        memo_type = MemoType.objects.create(name=name, code=code)
        return JsonResponse({
            'id': memo_type.id,
            'name': str(memo_type),
            'value': memo_type.id
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def create_category_ajax(request):
    """AJAX endpoint to create a new category"""
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        category_type = data.get('category_type', '').strip()
        
        if not name or not category_type:
            return JsonResponse({'error': 'Name and category type are required'}, status=400)
        
        # Validate category type
        valid_types = [choice[0] for choice in MemoCategory.CATEGORY_TYPES]
        if category_type not in valid_types:
            return JsonResponse({'error': f'Invalid category type. Choose from: {", ".join(valid_types)}'}, status=400)
        
        category = MemoCategory.objects.create(name=name, category_type=category_type)
        return JsonResponse({
            'id': category.id,
            'name': str(category),
            'value': category.id,
            'category_type': category_type
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def create_department_ajax(request):
    """AJAX endpoint to create a new department"""
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            name = data.get('name', '').strip()
            code = data.get('code', '').strip().upper()
            
            if not name or not code:
                return JsonResponse({'error': 'Name and code are required'}, status=400)
            
            # Check if code already exists
            if Department.objects.filter(code=code).exists():
                return JsonResponse({'error': f'Department with code "{code}" already exists'}, status=400)
            
            # Check if name already exists
            if Department.objects.filter(name__iexact=name).exists():
                return JsonResponse({'error': f'Department with name "{name}" already exists'}, status=400)
            
            department = Department.objects.create(
                name=name, 
                code=code,
                is_active=True
            )
            return JsonResponse({
                'id': department.id,
                'name': str(department),
                'value': department.id,
                'code': department.code
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)