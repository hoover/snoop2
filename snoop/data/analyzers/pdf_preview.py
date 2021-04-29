"""Task to call a service that creates pdf previews for various types of documents.

The service used can be found here: [[https://github.com/thecodingmachine/gotenberg]]
"""

from .. import models
from django.conf import settings
import requests
from ..tasks import snoop_task, SnoopTaskBroken, returns_json_blob

log = logging.getLogger(__name__)

PDF_PREVIEW_MIME_TYPES = {}
"""List of mime types that the pdf generator supports.
Based on [[insert link here]]
"""


def can_create(blob):
    """Checks if pdf generator can process this file."""
    if blob.mime_type in PDF_PREVIEW_MIME_TYPES:
        return True


def call_pdf_generator(data):
    """Executes HTTP PUT request to pdf generator service."""

    url = settings.PDF_PREVIEW_URL + '/convert/office'

    resp = requests.post(url, files={'files': data})

    if resp.status_code == 504:
        raise SnoopTaskBroken('pdf generator timed out and returned http 500', 'pdf_previe_http_500')

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

    with blob.open() as f:
        resp = call_pdf_generator(f)
    blob_pdf_preview = models.Blob.create_from_bytes(resp)
    # create PDF object in pdf preview model
    _, _ = 
