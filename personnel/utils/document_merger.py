# personnel/utils/document_merger.py

import os
import io
import zipfile
import tempfile
import shutil
import logging
from datetime import datetime

from django.conf import settings

from PyPDF2 import PdfMerger, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


class DocumentMerger:
    """
    Merge multiple documents into a single PDF or ZIP file.
    """

    DOCUMENT_REQUIREMENTS = {
        'translator': {
            'freelance': ['loa', 'payment_claim', 'invoice'],
            'staff': ['passport', 'boarding_pass', 'ticket'],
        },
        'interpreter': {
            'freelance': ['passport', 'loa', 'payment_claim', 'ticket', 'ticket_receipt', 'boarding_pass'],
            'staff': ['passport', 'boarding_pass', 'ticket', 'ticket_receipt'],
        },
        'default': ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']
    }

    DOC_DISPLAY_NAMES = {
        'passport': 'Passport Copy',
        'loa': 'Letter of Assignment (LOA)',
        'boarding_pass': 'Boarding Pass',
        'payment_claim': 'Payment Claim',
        'ticket': 'Ticket',
        'ticket_receipt': 'Ticket Receipt',
        'invoice': 'Invoice',
    }

    DOCUMENT_ORDER = {
        'translator_freelance': ['loa', 'payment_claim', 'invoice'],
        'translator_staff': ['passport', 'boarding_pass', 'ticket'],
        'interpreter_freelance': ['passport', 'loa', 'payment_claim', 'ticket', 'ticket_receipt', 'boarding_pass'],
        'interpreter_staff': ['passport', 'boarding_pass', 'ticket', 'ticket_receipt'],
        'default': ['passport', 'boarding_pass', 'ticket', 'ticket_receipt']
    }

    def __init__(self, personnel):
        self.personnel = personnel
        self.required_docs = self._get_required_documents()
        self.documents = self._get_documents()
        self.missing_docs = self._get_missing_documents()

    def _get_required_documents(self):
        personnel_type = self.personnel.personnel_type
        subtype = None
        if personnel_type == 'translator':
            subtype = self.personnel.translator_type
        elif personnel_type == 'interpreter':
            subtype = self.personnel.interpreter_type

        if personnel_type in self.DOCUMENT_REQUIREMENTS:
            if subtype in self.DOCUMENT_REQUIREMENTS[personnel_type]:
                return self.DOCUMENT_REQUIREMENTS[personnel_type][subtype]
            elif personnel_type == 'translator':
                return self.DOCUMENT_REQUIREMENTS['translator']['freelance']
            elif personnel_type == 'interpreter':
                return self.DOCUMENT_REQUIREMENTS['interpreter']['freelance']
        return self.DOCUMENT_REQUIREMENTS['default']

    def _get_documents(self):
        docs = {}
        for doc in self.personnel.documents.all():
            docs[doc.document_type] = doc
        return docs

    def _get_missing_documents(self):
        missing = []
        for doc_type in self.required_docs:
            if doc_type not in self.documents:
                missing.append(doc_type)
        return missing

    def has_all_documents(self):
        return len(self.missing_docs) == 0

    def get_missing_documents_display(self):
        return [self.DOC_DISPLAY_NAMES.get(doc, doc.title().replace('_', ' ')) for doc in self.missing_docs]

    def get_document_order(self):
        personnel_type = self.personnel.personnel_type
        subtype = None
        if personnel_type == 'translator':
            subtype = self.personnel.translator_type or 'freelance'
            key = f'translator_{subtype}'
        elif personnel_type == 'interpreter':
            subtype = self.personnel.interpreter_type or 'freelance'
            key = f'interpreter_{subtype}'
        else:
            key = 'default'
        return self.DOCUMENT_ORDER.get(key, self.DOCUMENT_ORDER['default'])

    def _convert_image_to_pdf(self, file_path):
        try:
            img = PILImage.open(file_path)
            pdf_path = file_path.rsplit('.', 1)[0] + '_converted.pdf'
            img.convert('RGB').save(pdf_path, 'PDF')
            return pdf_path
        except Exception as e:
            logger.error(f"Error converting image to PDF: {e}")
            return None

    def _convert_to_pdf(self, file_path, doc_type):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return self._convert_image_to_pdf(file_path)
        return file_path

    def _get_document_file_path(self, doc):
        if doc.file and os.path.exists(doc.file.path):
            return doc.file.path
        return None

    def _create_cover_page(self, output_path):
        try:
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4

            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(width / 2, height - 80, "DCMP MANAGEMENT")
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width / 2, height - 120, "DOCUMENT PACKAGE")

            c.setStrokeColor(colors.HexColor('#1B5E20'))
            c.setLineWidth(3)
            c.line(100, height - 140, width - 100, height - 140)

            c.setFont("Helvetica-Bold", 14)
            y_pos = height - 180
            c.drawString(100, y_pos, "PERSONNEL INFORMATION")

            c.setFont("Helvetica", 12)
            y_pos -= 30
            info_lines = [
                f"Name: {self.personnel.full_name()}",
                f"Type: {self.personnel.get_personnel_type_display()}",
                f"Nationality: {self.personnel.nationality}",
                f"Email: {self.personnel.email}",
                f"Phone: {self.personnel.phone}",
                f"Meeting: {self.personnel.meeting.name if self.personnel.meeting else 'Not assigned'}",
                f"Date Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}"
            ]
            for line in info_lines:
                c.drawString(100, y_pos, line)
                y_pos -= 20

            y_pos -= 30
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, y_pos, "DOCUMENTS INCLUDED")

            y_pos -= 30
            c.setFont("Helvetica", 12)
            for doc_type in self.get_document_order():
                if doc_type in self.documents:
                    name = self.DOC_DISPLAY_NAMES.get(doc_type, doc_type.title().replace('_', ' '))
                    c.drawString(120, y_pos, f"[X] {name}")
                    y_pos -= 20

            c.setFont("Helvetica-Oblique", 9)
            c.drawCentredString(width / 2, 40, "Generated by DCMP Management System")

            c.save()
            return True
        except Exception as e:
            logger.error(f"Error creating cover page: {e}")
            return False

    def merge_to_pdf(self, output_filename=None):
        if not self.has_all_documents():
            missing = self.get_missing_documents_display()
            return False, None, f"Missing documents: {', '.join(missing)}"

        if output_filename is None:
            safe_name = self.personnel.full_name().replace(' ', '_').replace('/', '_')
            output_filename = f"{safe_name}_merged_documents.pdf"

        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'

        temp_dir = tempfile.mkdtemp()
        try:
            cover_path = os.path.join(temp_dir, 'cover.pdf')
            if not self._create_cover_page(cover_path):
                return False, None, "Failed to create cover page"

            merger = PdfMerger()
            try:
                merger.append(cover_path)
            except Exception as e:
                logger.error(f"Error adding cover page: {e}")

            temp_pdfs = []
            for doc_type in self.get_document_order():
                if doc_type in self.documents:
                    doc = self.documents[doc_type]
                    file_path = self._get_document_file_path(doc)
                    if not file_path:
                        continue
                    pdf_path = self._convert_to_pdf(file_path, doc_type)
                    if pdf_path and pdf_path != file_path:
                        temp_pdfs.append(pdf_path)
                    if pdf_path and os.path.exists(pdf_path):
                        try:
                            reader = PdfReader(pdf_path)
                            if len(reader.pages) > 0:
                                merger.append(reader)
                        except Exception as e:
                            logger.error(f"Error merging {doc_type}: {e}")

            output_dir = os.path.join(settings.MEDIA_ROOT, 'merged_documents')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)

            merger.write(output_path)
            merger.close()

            for temp_pdf in temp_pdfs:
                try:
                    os.remove(temp_pdf)
                except Exception:
                    pass

            return True, output_path, None
        except Exception as e:
            logger.error(f"Error merging documents: {e}", exc_info=True)
            return False, None, str(e)
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

    def create_zip_package(self, output_filename=None):
        success, pdf_path, error = self.merge_to_pdf()
        if not success:
            return False, None, f"PDF merge failed: {error}"

        if output_filename is None:
            safe_name = self.personnel.full_name().replace(' ', '_').replace('/', '_')
            output_filename = f"{safe_name}_documents.zip"
        if not output_filename.endswith('.zip'):
            output_filename += '.zip'

        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(pdf_path, os.path.basename(pdf_path))
                zip_file.writestr('README.txt', self._generate_readme())

            output_dir = os.path.join(settings.MEDIA_ROOT, 'merged_documents')
            os.makedirs(output_dir, exist_ok=True)
            zip_output_path = os.path.join(output_dir, output_filename)
            with open(zip_output_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
            return True, zip_output_path, None
        except Exception as e:
            logger.error(f"Error creating ZIP: {e}", exc_info=True)
            return False, None, str(e)

    def _generate_readme(self):
        readme = f"""DCMP MANAGEMENT - DOCUMENT PACKAGE
=====================================

Personnel: {self.personnel.full_name()}
Type: {self.personnel.get_personnel_type_display()}
Nationality: {self.personnel.nationality}
Email: {self.personnel.email}
Phone: {self.personnel.phone}
Meeting: {self.personnel.meeting.name if self.personnel.meeting else 'Not assigned'}

Documents Included:
"""
        for i, doc_type in enumerate(self.get_document_order(), 1):
            if doc_type in self.documents:
                name = self.DOC_DISPLAY_NAMES.get(doc_type, doc_type.title().replace('_', ' '))
                readme += f"{i}. {name}\n"
        readme += f"\nGenerated: {datetime.now().strftime('%B %d, %Y at %H:%M')}\n"
        readme += "Generated by DCMP Management System\n"
        return readme

    def merge_and_download(self, format='pdf'):
        if format == 'pdf':
            success, path, error = self.merge_to_pdf()
        else:
            success, path, error = self.create_zip_package()

        if success and path:
            with open(path, 'rb') as f:
                content = f.read()
            filename = os.path.basename(path)
            return True, content, filename, None
        return False, None, None, error

    def get_document_status(self):
        status = {}
        for idx, doc_type in enumerate(self.get_document_order(), 1):
            if doc_type in self.documents:
                doc = self.documents[doc_type]
                status[doc_type] = {
                    'present': True,
                    'name': self.DOC_DISPLAY_NAMES.get(doc_type, doc_type.title().replace('_', ' ')),
                    'uploaded': doc.upload_date.strftime('%Y-%m-%d %H:%M') if doc.upload_date else 'Unknown',
                    'file_name': doc.file_name or doc.file.name,
                    'verified': doc.is_verified,
                    'order': idx
                }
            else:
                status[doc_type] = {
                    'present': False,
                    'name': self.DOC_DISPLAY_NAMES.get(doc_type, doc_type.title().replace('_', ' ')),
                    'uploaded': None,
                    'file_name': None,
                    'verified': False,
                    'order': idx
                }
        return status

    def get_merge_summary(self):
        doc_order = self.get_document_order()
        total_required = len(doc_order)
        total_present = sum(1 for doc in doc_order if doc in self.documents)
        return {
            'personnel_name': self.personnel.full_name(),
            'personnel_type': self.personnel.get_personnel_type_display(),
            'required_documents': doc_order,
            'required_documents_display': [self.DOC_DISPLAY_NAMES.get(doc, doc.title().replace('_', ' ')) for doc in doc_order],
            'total_required': total_required,
            'total_present': total_present,
            'has_all': self.has_all_documents(),
            'missing_documents': self.missing_docs,
            'missing_documents_display': self.get_missing_documents_display(),
            'document_status': self.get_document_status()
        }

    def has_merged_pdf(self):
        safe_name = self.personnel.full_name().replace(' ', '_').replace('/', '_')
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'merged_documents', f"{safe_name}_merged_documents.pdf")
        return os.path.exists(pdf_path)

    def get_merged_pdf_path(self):
        safe_name = self.personnel.full_name().replace(' ', '_').replace('/', '_')
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'merged_documents', f"{safe_name}_merged_documents.pdf")
        return pdf_path if os.path.exists(pdf_path) else None