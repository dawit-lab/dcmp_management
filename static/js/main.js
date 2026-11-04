// static/js/main.js

$(document).ready(function() {
    // Initialize DataTables
    if ($.fn.DataTable) {
        $('.datatable').DataTable({
            pageLength: 25,
            responsive: true,
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
            }
        });
    }
    
    // Auto-hide alerts
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
    
    // Confirm actions
    $('.confirm-action').on('click', function(e) {
        if (!confirm('Are you sure you want to perform this action?')) {
            e.preventDefault();
        }
    });
    
    // File input preview
    $('input[type="file"]').on('change', function() {
        const fileName = $(this).val().split('\\').pop();
        const label = $(this).siblings('.form-label');
        if (label.length) {
            label.text(fileName || 'No file chosen');
        }
    });
    
    // Document upload progress
    $('#upload-form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.prop('disabled', true);
        submitBtn.html('<span class="spinner-border spinner-border-sm"></span> Uploading...');
    });
});

// Helper Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showToast(message, type = 'success') {
    const toast = `
        <div class="toast-container position-fixed bottom-0 end-0 p-3">
            <div class="toast show bg-${type} text-white">
                <div class="toast-body">
                    ${message}
                    <button type="button" class="btn-close btn-close-white float-end" data-bs-dismiss="toast"></button>
                </div>
            </div>
        </div>
    `;
    $('body').append(toast);
    setTimeout(() => {
        $('.toast-container').remove();
    }, 5000);
}

// Document Management
function deleteDocument(docId) {
    if (confirm('Are you sure you want to delete this document?')) {
        fetch(`/api/documents/${docId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                showToast('Document deleted successfully');
                location.reload();
            } else {
                showToast('Error deleting document', 'danger');
            }
        })
        .catch(error => {
            showToast('Error: ' + error, 'danger');
        });
    }
}

// Payment Management
function approvePayment(paymentId) {
    if (confirm('Approve this payment?')) {
        fetch(`/api/payments/${paymentId}/approve/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            showToast(data.message || 'Payment approved successfully');
            location.reload();
        })
        .catch(error => {
            showToast('Error: ' + error, 'danger');
        });
    }
}

function markPaymentPaid(paymentId) {
    const reference = prompt('Enter payment reference number:');
    if (reference) {
        fetch(`/api/payments/${paymentId}/mark-paid/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reference: reference })
        })
        .then(response => response.json())
        .then(data => {
            showToast(data.message || 'Payment marked as paid');
            location.reload();
        })
        .catch(error => {
            showToast('Error: ' + error, 'danger');
        });
    }
}

// Personnel Management
function sendReminder(personnelId) {
    if (confirm('Send document reminder to this personnel?')) {
        fetch(`/api/personnel/${personnelId}/send-reminder/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast('Reminder sent successfully');
            } else {
                showToast('Error: ' + (data.message || 'Failed to send reminder'), 'danger');
            }
        })
        .catch(error => {
            showToast('Error sending reminder: ' + error, 'danger');
        });
    }
}

function sendToFinance(personnelId) {
    if (confirm('Send this personnel\'s documents to finance?')) {
        fetch(`/api/personnel/${personnelId}/send-to-finance/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToast('Error: ' + data.error, 'danger');
            } else {
                showToast(data.message || 'Sent to finance successfully');
                location.reload();
            }
        })
        .catch(error => {
            showToast('Error: ' + error, 'danger');
        });
    }
}