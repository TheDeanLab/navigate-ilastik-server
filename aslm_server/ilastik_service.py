import base64
from flask import Blueprint, request, escape, send_file

from os.path import exists
from io import BytesIO

import numpy

from ilastik import app

bp = Blueprint('ilastik', __name__, url_prefix='/ilastik')

class IlastikService:
    def __init__(self):
        self.ilastikShell = None
        self.exportArgs = None
        self.inputArgs = None

    def loadProjectFile(self, fileName):
        parser = app._argparser()

        known, unknown = parser.parse_known_args(['--headless', '--project='+fileName]) #, '--logfile=ilastik.log'])

        try:
            self.ilastikShell = app.main(known, unknown)

            #export config
            self.exportArgs, unknown = self.ilastikShell.projectManager.workflow.dataExportApplet.parse_known_cmdline_args(['--export_source=Simple Segmentation'])
            self.ilastikShell.projectManager.workflow.dataExportApplet.configure_operator_with_parsed_args(self.exportArgs)
            #input config
            self.inputArgs, unknown = self.ilastikShell.projectManager.workflow.batchProcessingApplet.parse_known_cmdline_args([])
        except:
            return False
        return True
    
    def segmentImage(self, preloaded_array=None, fileName=''):
        # self.inputArgs.raw_data = [fileName]
        if preloaded_array is not None:
            self.inputArgs.raw_data = ['preloaded_array']
            self.ilastikShell.projectManager.workflow.dataSelectionApplet.preloaded_array = preloaded_array
        else:
            self.inputArgs.raw_data = [fileName]
        return self.ilastikShell.projectManager.workflow.batchProcessingApplet.run_export_from_parsed_args(self.inputArgs)

ilastik_module = IlastikService()

def send_np_array(data):
    """Send a numpy array to the client side   
    """
    buf = BytesIO()
    numpy.savez_compressed(buf, data)
    buf.seek(0)

    return send_file(
        buf, 
        mimetype='application/octet-stream')


@bp.route('/load')
def load_pretrained_project():
    """Load a pixelClassification ilastik project file

    Returns
    -------
    success or fail message: string
        'Success' or other error messages
        error code: 500
        success code: 200
    """
    project_name = escape(request.args.get('project'))
    if not exists(project_name):
        return "Project file does not exist", 500
    try:
        if ilastik_module.loadProjectFile(project_name):
            return "Success"
        else:
            return "Couldn't load the project file", 500
    except:
        return "Couldn't load the project file", 500

@bp.route('/segmentation', methods=['POST'])
def get_segmentation():
    """Segment the passed image

    Returns
    -------
    segmentation mask array
        error code: 400, 500
        success code: 200
    """
    if 'image' not in request.json or 'dtype' not in request.json or 'shape' not in request.json:
        return 'json data is not correct', 400
    img_data = request.json['image']
    img_dtype = request.json['dtype']
    img_shape = request.json['shape']
    try:
        img_data = numpy.frombuffer(base64.b64decode(img_data), dtype=img_dtype).reshape(img_shape)
        r = ilastik_module.segmentImage(preloaded_array=img_data)
        return send_np_array(r[0])
    except:
        return 'internal error', 500
