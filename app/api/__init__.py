from flask import Blueprint

api_bp = Blueprint(
    'api_bp',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/api'
)

from . import api_functions
from . import api_change_functions
from . import api_cmdb_functions
from . import api_dashboard_functions
from . import api_lookup_table_functions
from . import api_idea_functions
from . import api_incident_problem_functions
from . import api_knowledge_functions
from . import api_people_functions
from . import api_sla_functions
from . import api_network_visualisation_functions
