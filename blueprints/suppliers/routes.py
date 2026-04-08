"""Suppliers blueprint — routes for supplier management."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from blueprints.suppliers import suppliers_bp
from decorators import supervisor_required
from extensions import db
from models import Part, Supplier
