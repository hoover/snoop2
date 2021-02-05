from urllib.parse import urljoin
import requests

# TODO: put NLP_SERVICE_URL into snoop settings
NLP_SERVICE_URL = 'http://127.0.0.1:5001/'


def call_nlp_server(endpoint, data_dict):
    url = urljoin(NLP_SERVICE_URL, endpoint)
    resp = requests.post(url, json=data_dict)
    if (resp.status_code != 200):
        raise RuntimeError(f'Unexpected response from nlp service: {resp.content}')
    return resp


def get_entities(text, language=None):
    data = {'text': text}
    if language:
        data['language'] = language
    resp = call_nlp_server('entity_extraction', data)
    entity_list = resp.json()
    return entity_list


def get_language(text):
    data = {'text': text}
    resp = call_nlp_server('language_detection', data)
    language = resp.json()['language']
    return language
