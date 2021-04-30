"""Task to call a service that creates pdf previews for various types of documents.

The service used can be found here: [[https://github.com/thecodingmachine/gotenberg]]
"""

from .. import models
from django.conf import settings
import requests
from ..tasks import snoop_task, SnoopTaskBroken, returns_json_blob


PDF_PREVIEW_MIME_TYPES = {
    'text/plain',
    'text/rtf',
    'application/msword',
    'vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msexcel',
    'vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/mspowerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.oasis.opendocument.presentation',
    'application/vnd.oasis.opendocument.spreadsheet',
    'application/vnd.oasis.opendocument.text',
}
"""List of mime types that the pdf generator supports.
Based on [[https://thecodingmachine.github.io/gotenberg/#office.basic]].
"""


def can_create(blob):
    """Checks if pdf generator can process this file."""
    if blob.mime_type in PDF_PREVIEW_MIME_TYPES:
        return True


def call_pdf_generator(data, filename):
    """Executes HTTP PUT request to pdf generator service."""

    url = settings.SNOOP_PDF_PREVIEW_URL + 'convert/office'
    print(url)

    resp = requests.post(url, files={'files': (filename, data)})

    if resp.status_code == 504:
        raise SnoopTaskBroken('pdf generator timed out and returned http 504', 'pdf_previe_http_504')

    if (resp.status_code != 200
            or resp.headers['Content-Type'] != 'application/pdf'):
        raise RuntimeError(f'Unexpected response from pdf generator: {resp}')

    return resp.content


@snoop_task('pdf_preview.get_pdf')
# the @returns_json_blob decorator is only needed to check if this function ran in digests.gather
@returns_json_blob
def get_pdf(blob):
    """Calls the pdf generator for a given blob.

    Adds the pdf preview to the database
    """

    filename = models.File.objects.get(original=blob.pk).name
    print('Filename:')
    print(filename)

    with blob.open() as f:
        resp = call_pdf_generator(f, filename)
    blob_pdf_preview = models.Blob.create_from_bytes(resp)
    # create PDF object in pdf preview model
    _, _ = models.PdfPreview.objects.update_or_create(
        blob=blob,
        defaults={'pdf_preview': blob_pdf_preview}
    )
