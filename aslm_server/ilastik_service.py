import base64
from os.path import exists
from io import BytesIO

from flask import Blueprint, request, escape, send_file

import numpy
import vigra
from ilastik import app
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.dataSelection.opDataSelection import PreloadedArrayDatasetInfo

bp = Blueprint('ilastik', __name__, url_prefix='/ilastik')

class IlastikService:
    def __init__(self):
        self.ilastikShell = None

    def loadProjectFile(self, fileName):
        parser = app._argparser()

        known, unknown = parser.parse_known_args(['--headless', '--project='+fileName]) #, '--logfile=ilastik.log'])

        try:
            self.ilastikShell = app.main(known, unknown)

            #export config
            exportArgs, unknown = self.ilastikShell.projectManager.workflow.dataExportApplet.parse_known_cmdline_args(['--export_source=Simple Segmentation'])
            self.ilastikShell.projectManager.workflow.dataExportApplet.configure_operator_with_parsed_args(exportArgs)
        except:
            return False
        return isinstance(self.ilastikShell.workflow, PixelClassificationWorkflow)
    
    def segmentImage(self, image_data):
        # may need to tag the data array
        # input_data = vigra.taggedView(input_data, "yxc")
        role_data_dict = [{
            'Raw Data':PreloadedArrayDatasetInfo(preloaded_array=image_data),
            # 'Prediction Mask': None
            }]
        return self.ilastikShell.projectManager.workflow.batchProcessingApplet.run_export(role_data_dict, export_to_array=True)

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
        r = ilastik_module.segmentImage(img_data)
        return send_np_array(r[0])
    except:
        return 'internal error', 500
