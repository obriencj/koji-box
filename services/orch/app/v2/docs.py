#!/usr/bin/env python3
"""
V2 Documentation API - API documentation and examples
"""

import logging
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)
docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/')
def api_documentation():
    """Get comprehensive API documentation"""
    return jsonify({
        'service': 'orch-service',
        'version': '2.0.0',
        'description': 'Resource Management System with Container-Based Access Control',
        'endpoints': {
            'resource': {
                'checkout': {
                    'method': 'POST',
                    'path': '/api/v2/resource/<uuid>',
                    'description': 'Checkout a resource by UUID',
                    'parameters': {
                        'uuid': {
                            'type': 'string',
                            'format': 'uuid',
                            'description': 'Resource UUID',
                            'required': True
                        }
                    },
                    'responses': {
                        '200': {
                            'description': 'Resource file downloaded',
                            'content_type': 'application/octet-stream'
                        },
                        '400': {
                            'description': 'Validation error or container identification failed'
                        },
                        '404': {
                            'description': 'Resource not found'
                        },
                        '409': {
                            'description': 'Resource already checked out'
                        },
                        '500': {
                            'description': 'Internal server error'
                        }
                    },
                    'example': {
                        'request': 'POST /api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                        'response': 'Binary file download'
                    }
                },
                'release': {
                    'method': 'DELETE',
                    'path': '/api/v2/resource/<uuid>',
                    'description': 'Release a resource by UUID',
                    'parameters': {
                        'uuid': {
                            'type': 'string',
                            'format': 'uuid',
                            'description': 'Resource UUID',
                            'required': True
                        }
                    },
                    'responses': {
                        '200': {
                            'description': 'Resource released successfully'
                        },
                        '400': {
                            'description': 'Validation error or resource not checked out to this container'
                        },
                        '404': {
                            'description': 'Resource not found'
                        },
                        '500': {
                            'description': 'Internal server error'
                        }
                    },
                    'example': {
                        'request': 'DELETE /api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                        'response': '{"message": "Resource released successfully"}'
                    }
                },
                'status': {
                    'method': 'GET',
                    'path': '/api/v2/resource/<uuid>/status',
                    'description': 'Get status of a resource by UUID',
                    'parameters': {
                        'uuid': {
                            'type': 'string',
                            'format': 'uuid',
                            'description': 'Resource UUID',
                            'required': True
                        }
                    },
                    'responses': {
                        '200': {
                            'description': 'Resource status information'
                        },
                        '400': {
                            'description': 'Validation error'
                        },
                        '404': {
                            'description': 'Resource not found'
                        },
                        '500': {
                            'description': 'Internal server error'
                        }
                    },
                    'example': {
                        'request': 'GET /api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890/status',
                        'response': '{"status": {"checked_out": true, "container_id": "abc123"}}'
                    }
                },
                'validate': {
                    'method': 'GET',
                    'path': '/api/v2/resource/<uuid>/validate',
                    'description': 'Validate if current client can access a resource',
                    'parameters': {
                        'uuid': {
                            'type': 'string',
                            'format': 'uuid',
                            'description': 'Resource UUID',
                            'required': True
                        }
                    },
                    'responses': {
                        '200': {
                            'description': 'Access validation result'
                        },
                        '400': {
                            'description': 'Validation error'
                        },
                        '500': {
                            'description': 'Internal server error'
                        }
                    },
                    'example': {
                        'request': 'GET /api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890/validate',
                        'response': '{"can_access": true}'
                    }
                }
            },
            'status': {
                'health': {
                    'method': 'GET',
                    'path': '/api/v2/status/health',
                    'description': 'Health check endpoint',
                    'responses': {
                        '200': {
                            'description': 'Service is healthy'
                        },
                        '500': {
                            'description': 'Service is unhealthy'
                        }
                    }
                },
                'mappings': {
                    'method': 'GET',
                    'path': '/api/v2/status/mappings',
                    'description': 'Get all resource mappings',
                    'responses': {
                        '200': {
                            'description': 'List of all resource mappings'
                        },
                        '500': {
                            'description': 'Internal server error'
                        }
                    }
                }
            }
        },
        'authentication': {
            'method': 'IP-based container identification',
            'description': 'Resources are accessed based on container IP address identification'
        },
        'resource_types': {
            'principal': {
                'description': 'Kerberos principal keytabs',
                'file_extension': '.keytab',
                'example': 'hub-admin@KOJI.BOX'
            },
            'worker': {
                'description': 'Koji worker keytabs with host registration',
                'file_extension': '.keytab',
                'example': 'koji-worker-1',
                'scaling': 'Supports scale index for scaled workers'
            },
            'cert': {
                'description': 'SSL certificates',
                'file_extension': '.crt',
                'example': 'koji-hub.koji.box'
            },
            'key': {
                'description': 'SSL private keys',
                'file_extension': '.key',
                'example': 'koji-hub.koji.box'
            }
        },
        'error_codes': {
            'VALIDATION_ERROR': 'Input validation failed',
            'RESOURCE_NOT_FOUND': 'Resource or resource mapping not found',
            'RESOURCE_ALREADY_CHECKED_OUT': 'Resource is already checked out to another container',
            'CONTAINER_NOT_FOUND': 'Unable to identify requesting container',
            'CONTAINER_NOT_RUNNING': 'Requesting container is not running',
            'RESOURCE_CREATION_FAILED': 'Failed to create the actual resource',
            'DATABASE_ERROR': 'Database operation failed',
            'CONTAINER_CLIENT_ERROR': 'Container client operation failed',
            'INTERNAL_ERROR': 'Internal server error'
        }
    })

@docs_bp.route('/examples')
def api_examples():
    """Get API usage examples"""
    return jsonify({
        'examples': {
            'checkout_resource': {
                'description': 'Checkout a resource',
                'curl': 'curl -X POST http://orch-service:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890 -o resource.keytab',
                'python': '''
import requests

response = requests.post('http://orch-service:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890')
if response.status_code == 200:
    with open('resource.keytab', 'wb') as f:
        f.write(response.content)
'''
            },
            'release_resource': {
                'description': 'Release a resource',
                'curl': 'curl -X DELETE http://orch-service:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                'python': '''
import requests

response = requests.delete('http://orch-service:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890')
print(response.json())
'''
            },
            'check_status': {
                'description': 'Check resource status',
                'curl': 'curl http://orch-service:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890/status',
                'python': '''
import requests

response = requests.get('http://orch-service:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890/status')
print(response.json())
'''
            },
            'validate_access': {
                'description': 'Validate resource access',
                'curl': 'curl http://orch-service:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890/validate',
                'python': '''
import requests

response = requests.get('http://orch-service:5000/api/v2/resource/a1b2c3d4-e5f6-7890-abcd-ef1234567890/validate')
print(response.json())
'''
            }
        }
    })

# The end.
