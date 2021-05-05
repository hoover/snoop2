import pytest
from snoop.data.analyzers import pdf_preview
from conftest import TESTDATA, CollectionApiClient
from snoop.data import models

pytestmark = [pytest.mark.django_db]


def test_pdf_preview_service():
    test_doc = TESTDATA / './disk-files/word/sample-doc-file-for-testing-1.doc'
    with test_doc.open('rb') as f:
        pdf_preview.call_pdf_generator(f, 'sample-doc-file-for-testing-1.doc')


def test_pdf_preview_task(fakedata):
    root = fakedata.init()
    test_doc = TESTDATA / './disk-files/word/sample-doc-file-for-testing-1.doc'
    with test_doc.open('rb') as f:
        blob = fakedata.blob(f.read())

    fakedata.file(root, 'file.doc', blob)
    pdf_preview.get_pdf(blob)
    assert models.PdfPreview.objects.get(blob=blob).pdf_preview.size > 0


def test_pdf_preview_digested(fakedata, taskmanager, client):
    root = fakedata.init()
    test_doc = TESTDATA / './disk-files/word/sample-doc-file-for-testing-1.doc'
    with test_doc.open('rb') as f:
        blob = fakedata.blob(f.read())

    fakedata.file(root, 'file.doc', blob)

    taskmanager.run()

    api = CollectionApiClient(client)
    digest = api.get_digest(blob.pk)['content']

    assert digest['has-pdf-preview'] is True


def test_pdf_preview_api(fakedata, taskmanager, client):
    root = fakedata.init()

    test_doc = TESTDATA / './disk-files/word/sample-doc-file-for-testing-1.doc'
    with test_doc.open('rb') as f:
        blob = fakedata.blob(f.read())

    fakedata.file(root, 'file.doc', blob)
    taskmanager.run()

    api = CollectionApiClient(client)

    api.get_pdf_preview(blob.pk)
