from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(minimum_role):
    """Decorator: require login AND at least *minimum_role*."""
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.has_role_at_least(minimum_role):
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def admin_required(f):
    """Shortcut: admin only."""
    @wraps(f)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapped


def supervisor_required(f):
    """Shortcut: supervisor or admin."""
    @wraps(f)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_supervisor:
            abort(403)
        return f(*args, **kwargs)
    return wrapped


def technician_required(f):
    """Shortcut: technician, supervisor, or admin."""
    @wraps(f)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_technician:
            abort(403)
        return f(*args, **kwargs)
    return wrapped


def contractor_or_above(f):
    """Shortcut: contractor, technician, supervisor, or admin."""
    @wraps(f)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.has_role_at_least("contractor"):
            abort(403)
        return f(*args, **kwargs)
    return wrapped


def permission_required(module, operation="read"):
    """Decorator: require the user to have a specific CRUD permission."""
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.can(module, operation):
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator
