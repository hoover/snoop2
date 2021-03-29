from .. import models
from django.conf import settings
from urllib.parse import urljoin
import requests
from collections import defaultdict

NLP_SERVICE_URL = settings.NLP_SERVICE_URL


def call_nlp_server(endpoint, data_dict):
    url = urljoin(NLP_SERVICE_URL, endpoint)
    resp = requests.post(url, json=data_dict)
    if (resp.status_code != 200):
        raise RuntimeError(f'Unexpected response from nlp service: {resp.content}')
    return resp.json()


def get_entities(text, language=None):
    data = {'text': text}
    if language:
        data['language'] = language
    return call_nlp_server('entity_extraction', data)


def get_language(text):
    data = {'text': text}
    return call_nlp_server('language_detection', data)['language']


# Create all db entries which are related to that entity.
def create_db_entries(entity, model, language, text_source, digest):
    db_ent = models.Entity.objects.get_or_create(
        entity=entity['text'],
        type=entity['type'])
    models.EntityHit.objects.get_or_create(
        entity=db_ent,
        model=models.LanguageModel.objects.get(
            language=language, method=model),
        text_source=text_source,
        start=entity['start'],
        end=entity['end'],
        digest=digest)


def extract_enitities(text, text_source, digest):
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
    results = defaultdict([])
    if settings.EXTRACT_ENTITIES:
        text = rv.get('text', '')
        if text:
            results.update(extract_enitities(text, 'text', digest))
        if rv['ocrtext']:
            for ocr_name, ocrtext in rv.get('ocrtext'):
                if ocrtext:
                    ocr_results = extract_enitities(ocrtext, ocr_name, digest)
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
                    results[f'{ocr_name}_lan'] = get_language(ocrtext[:2500])
    return results
