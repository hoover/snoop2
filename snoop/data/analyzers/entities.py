"""Tasks for entity extraction and language detection.

"""


from .. import models
from django.conf import settings
import requests
from collections import defaultdict


def call_nlp_server(endpoint, data_dict):
    """Calls the nlp server with data at an endpoint

    Sends a request to the nlp service with a specified endpoint and a data load as json.
    The two endpoints are `language_detection` and `entity extraction` at the moment.
    The `data_dict` is a dictionary which contains the request. It needs to contain a key `text`
    and can optionally also contain a key `language`, if the language is already specified.
    The response of the service will be JSON, which is decoded before returning.

    Args:
        endpoint: The name of the server endpoint that's called.
        data_dict: A dictionary containing data for a post request.

    Returns:
        The parsed JSON-response of the server

    Raises:
        ConnectionError: If the server was not found
        RuntimeError: If the server returns with an unexpected result.
        NotImplementedError: If the server is not able to process the request.
    """
    url = f'{settings.SNOOP_NLP_URL}/{endpoint}'
    resp = requests.post(url, json=data_dict)
    if (resp.status_code == 404):
        raise ConnectionError(f'Server not found at {url}')
    if (resp.status_code == 500):
        raise NotImplementedError(f'Server cannot fulfill request {resp.json()}')
    if (resp.status_code != 200 or resp.headers['Content-Type'] != 'application/json'):
        raise RuntimeError(f"Unexpected response from nlp service: type:{resp}")
    return resp.json()


def get_entities(text, language=None):
    """ Gets all entities for a given text.

    Creates a dict from a string and requests entity extraction from the nlp service
    optionally, the language can be specified.
    returns the decoded JSON dict from the service response.

    Args:
        text: text for which the entities are to be extracted.
        language: an optional language code, telling the service which language
        to use in order to process the text, instead of figuring that out by
        itself.

    Returns:
        The response from the call to the NLP Server.
    """
    data = {'text': text}
    if language:
        data['language'] = language
    return call_nlp_server('entity_extraction', data)


def get_language(text):
    """Gets the language code for a given text.

    Creates a dict from a string and requests language detection from the nlp
    service.

    Args:
        text: The string for which the language should be detected.

    Returns:
        the language code from the service response.
    """
    data = {'text': text}
    return call_nlp_server('language_detection', data)['language']


def create_db_entries(entity, model, language, text_source, digest):
    """Creates all Database entries which are related to an entity.

    `get_or_create` is used for the entity, so that every entity is only once in
    the database. In the Hit, the information where that entity was found is stored.
    Args:
        entity: dict containing entity text and type as Strings.
        model: the name of the used model
        language: language code of the used model
        text_source: 'text' if the entity is not from OCR, the OCR-Source if it is.
        digst: The digest object where the entity was found in.

    Returns:
        The Id of the created (if created) entity.
    """
    engine = 'polyglot' if model.startswith('polyglot_') else 'spacy'
    db_ent, _ = models.Entity.objects.get_or_create(
        entity=entity['text'],
        type=models.EntityType.objects.get_or_create(type=entity['type'])[0]
    )
    models.EntityHit.objects.get_or_create(
        entity=db_ent,
        model=models.LanguageModel.objects.get_or_create(
            language_code=language,
            engine=engine,
            description=model)[0],
        text_source=text_source,
        start=entity['start'],
        end=entity['end'],
        digest=digest
    )
    return db_ent.id


def extract_enitities(text, text_source, digest):
    """Processes entity extraction and language detection for one text source.

    The service is called, the database entries are created
    and the IDs of all entities are received from the database.
    Also, a list of all entity types which occur in the document is created.

    Args:
        text: the text, from which the entities shall be extracted
        text_source: 'text' if it's from the text or the name of the OCR-Source
        if the text is from an OCR
        digest: The digest object for which entitity extraction is done.

    Returns:
        results: A dictionary containing all found entities, the IDs of all
        unique entities that were found, as well as keys for all entity types
        containing a list of all entities with that type.
    """
    nlp_response = get_entities(text)
    ents = nlp_response['entities']
    results = {}
    results['ent-ids'] = list(set([create_db_entries(entity, nlp_response['model'],
                                   nlp_response['language'], text_source, digest) for entity in ents]))
    results['lang'] = nlp_response['language']
    results['entities'] = [k['text'] for k in ents]
    unique_ents = set([(k['text'], k['type']) for k in ents])
    for entity_type in set(v['type'] for v in ents):
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

    Args:
        digest: The digest model for which the text sources are processed.
        rv: the return value dict, from which the text sources are extracted

    Returns:
        results: a dict with all results from the entity extraction of all text
        sources.
    """
    results = defaultdict(defaultvalue)
    if settings.EXTRACT_ENTITIES:
        text = rv.get('text', '')
        if text:
            results.update(extract_enitities(text, 'text', digest))
        if 'ocrtext' in rv:
            for ocr_name, ocrtext in rv.get('ocrtext').items():
                if ocrtext:
                    ocr_results = extract_enitities(ocrtext, ocr_name, digest)
                    results[f'{ocr_name}_lang'] = ocr_results['lang']
                    if 'entities' in results:
                        results['entities'].extend(ocr_results['entities'])
                        results['ent-ids'].extend(ocr_results['ent-ids'])
                        for k, v in ocr_results.items():
                            if k.startswith('entity-type.'):
                                results[k].extend(v)
                    else:
                        results.update(ocr_results)
    elif settings.DETECT_LANGUAGE:
        text = rv.get('text', '')[:2500]
        if text:
            results['lang'](get_language(text))
        if rv['ocrtext']:
            for ocr_name, ocrtext in rv.get('ocrtext').items():
                if ocrtext:
                    results[f'{ocr_name}_lang'] = get_language(ocrtext[:2500])
    return results


def defaultvalue():
    """Function for defaultdict creating list by default
    """
    return []
