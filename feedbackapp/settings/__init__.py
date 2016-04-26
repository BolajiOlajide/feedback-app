"""
Settings package initialization.
"""

import envvars
envvars.load()

# Ensure development settings are not used in testing and production:
if not envvars.get('HEROKU'):
    from development import *

if envvars.get('HEROKU') is not None:
    from production import *

if envvars.get('TRAVIS') is not None:
    from base import *
