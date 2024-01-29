import os
import json
from pathlib import Path

from flask import Flask

def load_config():
    config_file_path = os.path.join(Path(__file__).resolve().parent, 'config.json')
    f_config = open(config_file_path)
    services = json.load(f_config)
    f_config.close()
    return services


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    # load service configuration from 'config.json' file.
    services = load_config()
    if services['Ilastik']:
        from . import ilastik_service
        app.register_blueprint(ilastik_service.bp)
        print('ilastik is started!')

    return app
