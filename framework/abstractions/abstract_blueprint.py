from abc import ABC
from flask import Blueprint as FlaskBlueprint
from quart import Blueprint as QuartBlueprint


class AbstractBlueprint(ABC, FlaskBlueprint, QuartBlueprint):
    pass
