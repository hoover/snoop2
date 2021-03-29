"""Tasks for entity extraction and language detection.
Entities are extracted by an nlp microservice. The service is called with  `call_nlp_server`.

"""


from .. import models
from django.conf import settings
from urllib.parse import urljoin
import requests
from collections import defaultdict

NLP_SERVICE_URL = settings.NLP_SERVICE_URL


def call_nlp_server(endpoint, data_dict):
    """Sends a request to the nlp service with a specified endpoint and a data load as json.
    The two endpoints are `language_detection` and `entity extraction` at the moment.
    The `data_dict` is a dictionary which contains the request. It needs to contain a key `text`
    and can optionally also contain a key `language`, if the language is already specified.
    The response of the service will be JSON, which is decoded before returning.
    """
    url = urljoin(NLP_SERVICE_URL, endpoint)
    resp = requests.post(url, json=data_dict)
    if (resp.status_code != 200):
        raise RuntimeError(f'Unexpected response from nlp service: {resp.content}')
    return resp.json()


def get_entities(text, language=None):
    """Creates a dict from a string and requests entity extraction from the nlp service
    optionally, the language can be specified.
    returns the decoded JSON dict from the service response.
    """
    data = {'text': text}
    if language:
        data['language'] = language
    return call_nlp_server('entity_extraction', data)


def get_language(text):
    """Creates a dict from a string and requests language detection from the nlp service
    returns the language code from the service response.
    """
    data = {'text': text}
    return call_nlp_server('language_detection', data)['language']


def create_db_entries(entity, model, language, text_source, digest):
    """Creates all Database entries which are related to an entity.
    The entity (with its type) is created if it doesn't exist yet.
    The entity arg is a dict containing the entity type and text,
    as well as its start and end index within the text in which the hit occurs.
    The entity Hit is created with all the needed info.

    """
    db_ent = models.Entity.objects.get_or_create(
        entity=entity['text'],
        type=entity['type'])
    models.EntityHit.objects.get_or_create(
        entity=db_ent,
        model=models.LanguageModel.objects.get_or_create(
            language=language, method=model),
        text_source=text_source,
        start=entity['start'],
        end=entity['end'],
        digest=digest)


def extract_enitities(text, text_source, digest):
    """Processes entity extraction and language detection for one text source.
    The service is called, the database entries are created
    and the IDs of all entities are received from the database.
    Also, a list of all entity types which occur in the document is created.
    All results are put in a dict and returned
    """
    nlp_response = get_entities(text)
    ents = nlp_response['entities']
    results = {}
    for entity in ents:
        create_db_entries(entity, nlp_response['method'],
                          nlp_response['language'], text_source, digest)
    results['lang'] = nlp_response['language']
    results['entities'] = [k['text'] for k in ents]
    unique_ents = set([(k['text'], k['type']) for k in ents])
    results['ent-ids'] = [models.Entity.objects.get(entity=k[0], type=k[1]).id
                          for k in unique_ents]
    for entity_type in set(v['type'] for v in results['entities']):
        results[f'entity-type.{entity_type}'] = [k[0] for k in unique_ents
                                                 if k[1] == entity_type]
    return results


def process_document(digest, rv):
    """Processes an entire document with possibly multiple text sources.
    If entitiy extraciton is turned on (default):
    All text source, `rv['text'] and all texts in rv['ocrtext']` are processed.
    The results are extended after each processed text source, in order to
    have a complete list of extracted entities and their IDs for a document.
    Additionally, the detected language is added for all text sources.
    If not:
    only the detected language is returned for all text sources.
    """
    results = defaultdict([])
    if settings.EXTRACT_ENTITIES:
        text = rv.get('text', '')
        if text:
            results.update(extract_enitities(text, 'text', digest))
        if rv['ocrtext']:
            for ocr_name, ocrtext in rv.get('ocrtext'):
                if ocrtext:
                    ocr_results = extract_enitities(ocrtext, ocr_name, digest)
                    results[f'{ocr_name}_lang'] = ocr_results['lang']
                    if 'entities' in results:
                        results['entities'].extend(ocr_results['entities'])
                        results['ent-ids'].extend(ocr_results['ent-ids'])
                        for k, v in ocr_results:
                            if k.startswith('entity-type.'):
                                results[k].extend(v)
                    else:
                        results.update(ocr_results)
    elif settings.DETECT_LANGUAGE:
        text = rv.get('text', '')[:2500]
        if text:
            results.update(get_language(text))
        if rv['ocrtext']:
            for ocr_name, ocrtext in rv.get('ocrtext'):
                if ocrtext:
                    results[f'{ocr_name}_lang'] = get_language(ocrtext[:2500])
    return results
