"""
storage.py — Firebase Storage helper.
Uploads receipt files and returns a public download URL.
"""

import os
import json
import uuid
import firebase_admin
from firebase_admin import credentials, storage


def init_firebase():
    """
    Initialise Firebase Admin SDK using credentials from environment variable.
    Safe to call multiple times — only initialises once.
    """
    if firebase_admin._apps:
        return  # Already initialised

    creds_json = os.environ.get('FIREBASE_CREDENTIALS')
    if not creds_json:
        raise RuntimeError("FIREBASE_CREDENTIALS environment variable is not set.")

    cred_dict = json.loads(creds_json)
    cred      = credentials.Certificate(cred_dict)

    firebase_admin.initialize_app(cred, {
        'storageBucket': os.environ['FIREBASE_STORAGE_BUCKET']
    })


def upload_receipt(file_stream, original_filename: str) -> str:
    """
    Upload a receipt file to Firebase Storage.

    Args:
        file_stream:       File-like object (from Flask's request.files)
        original_filename: Original filename from the customer's device

    Returns:
        Public download URL string (permanent, no expiry)

    Raises:
        RuntimeError: If upload fails
    """
    init_firebase()

    # Generate a unique filename to avoid collisions
    ext          = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'jpg'
    unique_name  = f"receipts/{uuid.uuid4().hex}.{ext}"

    bucket = storage.bucket()
    blob   = bucket.blob(unique_name)

    # Set content type based on extension
    content_types = {
        'jpg':  'image/jpeg',
        'jpeg': 'image/jpeg',
        'png':  'image/png',
        'pdf':  'application/pdf',
        'webp': 'image/webp',
    }
    content_type = content_types.get(ext, 'application/octet-stream')

    blob.upload_from_file(file_stream, content_type=content_type)

    # Make the file publicly readable so you can view it in the admin dashboard
    blob.make_public()

    return blob.public_url
