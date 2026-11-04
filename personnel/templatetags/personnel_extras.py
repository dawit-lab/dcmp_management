# personnel/templatetags/personnel_extras.py
# personnel/templatetags/personnel_extras.py

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
import json
from personnel.models import Document 

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    if key is None:
        return None
    if key in dictionary:
        return dictionary[key]
    return None

@register.filter
def get_doc(documents, doc_type):
    """
    Get a document from the documents list by document type.
    Usage: {{ documents|get_doc:doc_type }}
    """
    if not documents:
        return None
    for doc in documents:
        if doc.document_type == doc_type:
            return doc
    return None

@register.filter
@stringfilter
def split(value, delimiter=','):
    """
    Split a string by delimiter.
    Usage: {{ "a,b,c"|split:"," }}
    """
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter)]

@register.filter
@stringfilter
def split_string(value, delimiter=','):
    """
    Split a string by delimiter.
    Usage: {{ value|split_string:"," }}
    """
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter)]

@register.filter
def get_value(dictionary, key):
    """
    Get a value from a dictionary by key with fallback.
    Usage: {{ dictionary|get_value:key }}
    """
    if dictionary and key in dictionary:
        return dictionary[key]
    return None

@register.filter
def has_document(documents, doc_type):
    """
    Check if a document exists in the list.
    Usage: {{ documents|has_document:"passport" }}
    """
    if not documents:
        return False
    for doc in documents:
        if doc.document_type == doc_type:
            return True
    return False

@register.simple_tag
def get_document_url(documents, doc_type, url_name='view-document'):
    """
    Get the URL for a specific document type.
    Usage: {% get_document_url documents "passport" as doc_url %}
    """
    if not documents:
        return None
    for doc in documents:
        if doc.document_type == doc_type:
            from django.urls import reverse
            return reverse(url_name, args=[doc.id])
    return None

@register.filter
def get_document_by_type(documents, doc_type):
    """
    Get a document object by type.
    Usage: {{ documents|get_document_by_type:"passport" }}
    """
    if not documents:
        return None
    for doc in documents:
        if doc.document_type == doc_type:
            return doc
    return None

# from django import template

# register = template.Library()

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if total and total > 0:
            return int((value / total) * 100)
        return 0
    except (TypeError, ZeroDivisionError):
        return 0
    
@register.filter
def doc_label(doc_type):
    """Human-readable label for a document-type key.

    Usage:  {{ "payment_claim"|doc_label }}  ->  'Payment Claim'
    """
    if not doc_type:
        return ''
    return Document.DISPLAY_NAMES.get(
        doc_type,
        str(doc_type).replace('_', ' ').title()
    )    

# @register.filter
# def get_item(dictionary, key):
#     """Get item from dictionary by key"""
#     if dictionary is None:
#         return None
#     return dictionary.get(key)

# @register.filter
# def split(value, arg):
#     """Split a string by the given character"""
#     if value:
#         return value.split(arg)
#     return []

# @register.filter
# def get_document_label(document_type):
#     """Get human-readable label for document type"""
#     labels = {
#         'passport': 'Passport Copy',
#         'loa': 'Letter of Assignment (LOA)',
#         'boarding_pass': 'Boarding Pass',
#         'payment_claim': 'Payment Claim',
#         'ticket': 'Ticket',
#         'ticket_receipt': 'Ticket Receipt',
#         'invoice': 'Invoice',
#         'other': 'Other',
#     }
#     return labels.get(document_type, document_type.title())

# @register.filter
# def sum_lengths(iterable1, iterable2):
#     """Add the lengths of two iterables"""
#     return len(iterable1) + len(iterable2)

# @register.filter
# def total_personnel(translators, interpreters, coordination):
#     """Calculate total personnel count from three lists"""
#     return len(translators) + len(interpreters) + len(coordination)

# @register.filter
# def divide(value, arg):
#     """Divide value by arg. Returns 0 if arg is 0 or invalid."""
#     try:
#         value = float(value)
#         arg = float(arg)
#         if arg == 0:
#             return 0
#         return value / arg
#     except (ValueError, TypeError, ZeroDivisionError):
#         return 0

# @register.filter
# def multiply(value, arg):
#     """Multiply value by arg."""
#     try:
#         return float(value) * float(arg)
#     except (ValueError, TypeError):
#         return 0

# @register.filter
# def get_item(dictionary, key):
#     """Get item from dictionary."""
#     return dictionary.get(key)

# @register.filter
# def subtract(value, arg):
#     """Subtract arg from value"""
#     try:
#         return float(value) - float(arg)
#     except (ValueError, TypeError):
#         return 0

# @register.filter
# def add(value, arg):
#     """Add arg to value"""
#     try:
#         return float(value) + float(arg)
#     except (ValueError, TypeError):
#         return 0
    
# # personnel/templatetags/personnel_extras.py - Add this filter

# @register.filter
# def get_item(dictionary, key):
#     """Get an item from a dictionary by key"""
#     if dictionary and key in dictionary:
#         return dictionary[key]
#     return None