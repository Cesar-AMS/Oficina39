from __future__ import annotations

from flask import Blueprint, jsonify


public_api_bp = Blueprint('public_api', __name__, url_prefix='/api/public')


def _openapi_spec():
    return {
        'openapi': '3.0.3',
        'info': {
            'title': 'Oficina39 Public API',
            'version': '1.0.0',
            'description': 'API publica para integracoes externas com autenticacao por API Key e webhooks assinados.',
        },
        'servers': [
            {'url': '/'},
        ],
        'components': {
            'securitySchemes': {
                'ApiKeyHeader': {
                    'type': 'apiKey',
                    'in': 'header',
                    'name': 'X-API-Key',
                },
                'ApiSecretHeader': {
                    'type': 'apiKey',
                    'in': 'header',
                    'name': 'X-API-Secret',
                },
                'BearerAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT',
                },
            }
        },
        'paths': {
            '/api/public/health': {
                'get': {
                    'summary': 'Health check publico',
                    'responses': {
                        '200': {'description': 'Servico online'},
                    },
                }
            },
            '/api/integracoes/status': {
                'get': {
                    'summary': 'Status autenticado das integracoes',
                    'security': [{'ApiKeyHeader': [], 'ApiSecretHeader': []}, {'BearerAuth': []}],
                    'responses': {
                        '200': {'description': 'Integracoes operacionais'},
                        '401': {'description': 'Nao autenticado'},
                        '429': {'description': 'Rate limit excedido'},
                    },
                }
            },
            '/api/integracoes/cep/{cep}': {
                'get': {
                    'summary': 'Consulta de CEP',
                    'security': [{'ApiKeyHeader': [], 'ApiSecretHeader': []}, {'BearerAuth': []}],
                    'parameters': [
                        {'name': 'cep', 'in': 'path', 'required': True, 'schema': {'type': 'string'}},
                    ],
                    'responses': {
                        '200': {'description': 'CEP encontrado'},
                        '400': {'description': 'CEP invalido'},
                        '401': {'description': 'Nao autenticado'},
                    },
                }
            },
            '/api/integracoes/placa/{placa}': {
                'get': {
                    'summary': 'Consulta de placa',
                    'security': [{'ApiKeyHeader': [], 'ApiSecretHeader': []}, {'BearerAuth': []}],
                    'parameters': [
                        {'name': 'placa', 'in': 'path', 'required': True, 'schema': {'type': 'string'}},
                    ],
                    'responses': {
                        '200': {'description': 'Placa encontrada'},
                        '400': {'description': 'Placa invalida'},
                        '401': {'description': 'Nao autenticado'},
                    },
                }
            },
            '/api/webhooks': {
                'post': {
                    'summary': 'Cadastro administrativo de webhook',
                    'security': [{'BearerAuth': []}],
                    'responses': {
                        '201': {'description': 'Webhook criado'},
                        '403': {'description': 'Sem permissao'},
                    },
                }
            },
        },
    }


@public_api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'oficina39-public-api',
        'version': '1.0.0',
    })


@public_api_bp.route('/openapi.json', methods=['GET'])
def openapi():
    return jsonify(_openapi_spec())
