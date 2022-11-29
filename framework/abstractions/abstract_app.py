from abc import ABC
from flask import Flask
from quart import Quart


class AbstractServer(ABC, Flask, Quart):
    pass
