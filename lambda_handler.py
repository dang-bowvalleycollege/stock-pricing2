"""
Lambda handler for Stock Dashboard API
Wraps Flask app for AWS Lambda deployment
"""

import awsgi
from app import app


def handler(event, context):
    """AWS Lambda handler function"""
    return awsgi.response(app, event, context, base64_content_types={"image/png"})
