import pytest
from snoop.data.analyzers import thumbnails
from conftest import TESTDATA, CollectionApiClient
from snoop.data import models
from django.conf import settings

pytestmark = [pytest.mark.django_db]


def test_thumbnail_service():
    test_doc = TESTDATA / './no-extension/file_doc'
    with test_doc.open('rb') as f:
        thumbnails.call_thumbnails_service(f, 100)


def test_thumbnail_task():
    IMAGE = settings.SNOOP_TESTDATA + "/data/disk-files/images/bikes.jpg"
    image_blob = models.Blob.create_from_file(IMAGE)
    thumbnails.get_thumbnail(image_blob)
    assert models.Thumbnail.objects.get(size=100, blob=image_blob).thumbnail.size > 0


def test_thumbnail_digested(fakedata, taskmanager, client):
    root = fakedata.init()
    test_doc = TESTDATA / './no-extension/file_doc'
    with test_doc.open('rb') as f:
        blob = fakedata.blob(f.read())

    fakedata.file(root, 'file.doc', blob)

    taskmanager.run()

    api = CollectionApiClient(client)
    digest = api.get_digest(blob.pk)['content']

    assert digest['has-thumbnails'] is True


def test_thumbnail_api(fakedata, taskmanager, client):
    root = fakedata.init()

    test_pdf = TESTDATA / './no-extension/file_pdf'
    test_docx = TESTDATA / './no-extension/file_docx'
    test_jpg = TESTDATA / './no-extension/file_jpg'

    files = {'file.pdf': test_pdf,
             'file.docx': test_docx,
             'file.jpg': test_jpg,
             }

    for filename, testfile in files.items():
        with testfile.open('rb') as f:
            blob = fakedata.blob(f.read())
        fakedata.file(root, filename, blob)

        taskmanager.run(limit=1000)
        api = CollectionApiClient(client)

        for size in models.Thumbnail.SizeChoices.values:
            api.get_thumbnail(blob.pk, size)
