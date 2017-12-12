# -*- coding: utf-8 -*-
from .main import main_blueprint
from .dev import dev_blueprint
from .api import api_blueprint
from .login import login_blueprint
from .meeting import meeting_blueprint
from .sprint import sprint_blueprint

blueprints = [main_blueprint,
              dev_blueprint,
              api_blueprint,
              login_blueprint,
              meeting_blueprint,
              sprint_blueprint]
