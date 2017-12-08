# -*- coding: utf-8 -*-
from datetime import datetime
from app.models import Sprint


def register_processors(app):
    @app.context_processor
    def utility_processor():
        def aktiver_sprint():
            return Sprint.get_aktiv()

        def decode_date(date):
            if not date:
                return ""
            return date.strftime('%d.%m.%Y')

        def encode_date(date):
            try:
                return datetime.strptime(date, "%d.%m.%Y").date()
            except ValueError:
                return None

        return dict(aktiver_sprint=aktiver_sprint(),
                    decode_date=decode_date,
                    encode_date=encode_date)
