import base64
from os.path import exists
from io import BytesIO
import json

from flask import Blueprint, request, send_file
from markupsafe import escape

import numpy
import vigra
from ilastik import app
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.dataSelection.opDataSelection import PreloadedArrayDatasetInfo

bp = Blueprint('ilastik', __name__, url_prefix='/ilastik')

class IlastikService:
    def __init__(self):
        self.ilastikShell = None

    def convert_numpy_rgb(self, rgb_list):
        return ['#{:02x}{:02x}{:02x}'.format(rgb_color[0], rgb_color[1], rgb_color[2]) for rgb_color in rgb_list]

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
        label_info = None
        if isinstance(self.ilastikShell.workflow, PixelClassificationWorkflow):
            opPixelClassification = self.ilastikShell.projectManager.workflow.pcApplet.topLevelOperator
            label_info = {
                'names': opPixelClassification.LabelNames.value,
                'label_colors': self.convert_numpy_rgb(opPixelClassification.LabelColors.value),
                'segmentation_colors': self.convert_numpy_rgb(opPixelClassification.PmapColors.value)
            }
        return label_info
    
    def segmentImage(self, img_data):
        # may need to tag the data array
        # input_data = vigra.taggedView(input_data, "yxc")
        role_data_dict = [{
            'Raw Data':PreloadedArrayDatasetInfo(preloaded_array=img),
            # 'Prediction Mask': None
            } for img in img_data]
        return self.ilastikShell.projectManager.workflow.batchProcessingApplet.run_export(role_data_dict, export_to_array=True)

ilastik_module = IlastikService()

def send_np_array(data):
    """Send a numpy array to the client side   
    """
    buf = BytesIO()
    numpy.savez_compressed(buf, *data)
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
        r = ilastik_module.loadProjectFile(project_name)
        if r:
            return json.dumps(r)
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
        img_data = [numpy.frombuffer(base64.b64decode(img), dtype=img_dtype).reshape(img_shape) for img in img_data]
        r = ilastik_module.segmentImage(img_data)
        return send_np_array(r)
    except:
        return 'internal error', 500
