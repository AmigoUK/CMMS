"""File upload helpers."""

import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

from models.attachment import ALLOWED_EXTENSIONS

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def allowed_file(filename):
    """Check if filename has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def is_allowed_image(file):
    """Check if uploaded file has an allowed image MIME type and extension."""
    if not file or not file.filename:
        return False
    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
    return file.content_type in ALLOWED_IMAGE_TYPES and ext in {"jpg", "jpeg", "png", "gif", "webp"}


def generate_stored_filename(original_filename):
    """Generate a UUID-based filename preserving the original extension."""
    ext = ""
    if "." in original_filename:
        ext = "." + original_filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def save_attachment(file, entity_type, entity_id, uploaded_by_id=None):
    """Save an uploaded file and create an Attachment record.

    Returns the Attachment instance (already added to session, not committed).
    """
    from extensions import db
    from models.attachment import Attachment

    original_name = secure_filename(file.filename)
    stored_name = generate_stored_filename(original_name)

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, stored_name)
    file.save(filepath)

    file_size = os.path.getsize(filepath)

    attachment = Attachment(
        filename=original_name,
        stored_filename=stored_name,
        file_size=file_size,
        mime_type=file.content_type or "",
        entity_type=entity_type,
        entity_id=entity_id,
        uploaded_by_id=uploaded_by_id,
    )
    db.session.add(attachment)
    return attachment
