# -*- coding: utf-8 -*-
from .main import blueprint as main_blueprint
from .api import blueprint as api_blueprint
from .login import blueprint as login_blueprint
from .meeting import blueprint as meeting_blueprint
from .sprint import blueprint as sprint_blueprint

blueprints = [main_blueprint,
              api_blueprint,
              login_blueprint,
              meeting_blueprint,
              sprint_blueprint]
