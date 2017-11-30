# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

dev_blueprint = Blueprint('dev', __name__, url_prefix="/dev")


@dev_blueprint.route("/<fname>")
def page(fname):
    return render_template(f"{fname}.html")
