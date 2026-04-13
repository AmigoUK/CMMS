"""Contacts blueprint — address book for email recipients."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from blueprints.contacts import contacts_bp
from decorators import supervisor_required
from extensions import db
from models import Contact, Supplier, User, CONTACT_CATEGORIES


@contacts_bp.route("/")
@supervisor_required
def list_contacts():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", "")
    page = request.args.get("page", 1, type=int)

    query = Contact.query.filter(Contact.is_active == True)

    if cat and cat in CONTACT_CATEGORIES:
        query = query.filter(Contact.category == cat)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Contact.name.ilike(like),
                Contact.email.ilike(like),
                Contact.company.ilike(like),
            )
        )

    pagination = query.order_by(Contact.category, Contact.name).paginate(
        page=page, per_page=25, error_out=False,
    )

    return render_template(
        "contacts/index.html",
        contacts=pagination.items,
        pagination=pagination,
        search_query=q,
        category_filter=cat,
        categories=CONTACT_CATEGORIES,
    )


@contacts_bp.route("/new", methods=["GET"])
@supervisor_required
def new():
    return render_template("contacts/form.html", contact=None, categories=CONTACT_CATEGORIES)


@contacts_bp.route("/new", methods=["POST"])
@supervisor_required
def create():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not name or not email:
        flash("Name and email are required.", "danger")
        return redirect(url_for("contacts.new"))

    contact = Contact(
        name=name,
        email=email,
        phone=request.form.get("phone", "").strip(),
        company=request.form.get("company", "").strip(),
        category=request.form.get("category", "other"),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(contact)
    db.session.commit()
    flash(f"Contact '{name}' added.", "success")
    return redirect(url_for("contacts.list_contacts"))


@contacts_bp.route("/<int:id>/edit", methods=["GET"])
@supervisor_required
def edit(id):
    contact = Contact.query.get_or_404(id)
    return render_template("contacts/form.html", contact=contact, categories=CONTACT_CATEGORIES)


@contacts_bp.route("/<int:id>/edit", methods=["POST"])
@supervisor_required
def update(id):
    contact = Contact.query.get_or_404(id)
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not name or not email:
        flash("Name and email are required.", "danger")
        return redirect(url_for("contacts.edit", id=contact.id))

    contact.name = name
    contact.email = email
    contact.phone = request.form.get("phone", "").strip()
    contact.company = request.form.get("company", "").strip()
    contact.category = request.form.get("category", "other")
    contact.notes = request.form.get("notes", "").strip()

    if request.form.get("is_active") is not None:
        contact.is_active = request.form.get("is_active") == "1"

    db.session.commit()
    flash(f"Contact '{name}' updated.", "success")
    return redirect(url_for("contacts.list_contacts"))


@contacts_bp.route("/<int:id>/toggle", methods=["POST"])
@supervisor_required
def toggle(id):
    contact = Contact.query.get_or_404(id)
    contact.is_active = not contact.is_active
    db.session.commit()
    flash(f"Contact '{contact.name}' {'activated' if contact.is_active else 'deactivated'}.", "success")
    return redirect(url_for("contacts.list_contacts"))


@contacts_bp.route("/import-suppliers", methods=["POST"])
@supervisor_required
def import_suppliers():
    """Bulk import contacts from Supplier records."""
    suppliers = Supplier.query.filter(
        Supplier.is_active == True,
        Supplier.email != "",
    ).all()
    added = 0
    for s in suppliers:
        existing = Contact.query.filter_by(email=s.email).first()
        if not existing:
            c = Contact(
                name=s.contact_person or s.name,
                email=s.email,
                phone=s.phone,
                company=s.name,
                category="supplier",
            )
            db.session.add(c)
            added += 1
    db.session.commit()
    flash(f"{added} supplier contacts imported.", "success")
    return redirect(url_for("contacts.list_contacts"))


@contacts_bp.route("/import-users", methods=["POST"])
@supervisor_required
def import_users():
    """Bulk import contacts from User records."""
    users = User.query.filter(
        User.is_active_user == True,
        User.email != "",
    ).all()
    added = 0
    for u in users:
        existing = Contact.query.filter_by(email=u.email).first()
        if not existing:
            c = Contact(
                name=u.display_name,
                email=u.email,
                phone=u.phone,
                category="staff",
            )
            db.session.add(c)
            added += 1
    db.session.commit()
    flash(f"{added} staff contacts imported.", "success")
    return redirect(url_for("contacts.list_contacts"))
