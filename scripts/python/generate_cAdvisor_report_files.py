import logging.config
import os
from datetime import datetime, timedelta, timezone

import yaml
from prometheus_api_client import PrometheusConnect, MetricRangeDataFrame

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('generate_report_files')

# config file
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

APOLLO_NODE_IP = os.environ['APOLLO_NODE_IP']
PROMETHEUS_SERVER_PORT = os.environ['PROMETHEUS_SERVER_PORT']

APOLLO_PROMETHEUS_CLIENT = PrometheusConnect(url=f"http://{APOLLO_NODE_IP}:{PROMETHEUS_SERVER_PORT}",
                                             disable_ssl=True)

HOME_DIR = os.environ['HOME']

END_TIME = datetime.now(timezone.utc)  # Prometheus uses UTC
START_TIME = END_TIME - timedelta(hours=config['simulation']['time_delta'])

CADVISOR_METRIC_NAMES = config['cAdvisor']['container']['metric_names']

AMPHORA_RELATIVE_CHART_PATH = config['mkdocs']['report']['charts']['amphora_simulation']
EPHEMERAL_RELATIVE_CHART_PATH = config['mkdocs']['report']['charts']['ephemeral_simulation']
REPORT_PATH = os.path.join(HOME_DIR, config['mkdocs']['report']['services'])

AMPHORA_SIMULATION_CREATE_SECRET_GROUPS = config['simulation']['groups']['amphora']['createSecret']
AMPHORA_SIMULATION_GET_SECRET_GROUPS = config['simulation']['groups']['amphora']['getSecret']
AMPHORA_SIMULATION_DELETE_SECRET_GROUPS = config['simulation']['groups']['amphora']['deleteSecret']
EPHEMERAL_SIMULATION_GROUPS = config['simulation']['groups']['ephemeral']['execute']


def generate_markdown_file(simulation_groups_promQL, report_chart_path, report_path, metrics, service, request_name):
    """
    :param simulation_groups_promQL: query to retrieve simulation groups.
    :param report_chart_path: relative path to the response times chart.
    :param report_path: path to the report directory.
    :param metrics: cAdvisor metrics.
    :param service: name of the service.
    :param request_name: Carbyne Stack client request.
    """
    simulation_groups_dict = APOLLO_PROMETHEUS_CLIENT.custom_query_range(
        query=simulation_groups_promQL,
        start_time=START_TIME,
        end_time=END_TIME, step='15s')

    if len(simulation_groups_dict) > 0:
        simulation_groups_df = MetricRangeDataFrame(simulation_groups_dict)
        # gatling sends the same metric in a configured interval, e.g. 1min
        simulation_groups_df = simulation_groups_df.drop_duplicates()

        for group in simulation_groups_df['group'].drop_duplicates():
            markdown_content = "# cAdvisor\n\n"

            for metric in metrics:
                chart_file = f"{report_chart_path}/{service}/{service}_{group}_{metric}.png"
                markdown_content += f"## {metric}\n\n![Graph]({chart_file})\n\n"

                report_directory = f"{report_path}/{service}/{request_name}"
                filename = f"{report_directory}/{group}.md"

                try:
                    with open(filename, 'w') as file:
                        file.write(markdown_content)

                    logger.info(f"Generated {filename}")
                except Exception as e:
                    logger.error(f"Error: {e} for service: {service} and request: {request_name}")
    else:
        logger.error(f"No simulation groups found for service: {service} and query: {simulation_groups_promQL}")

# Create cAdvisor report for amphora createSecret request
generate_markdown_file(simulation_groups_promQL=AMPHORA_SIMULATION_CREATE_SECRET_GROUPS,
                       report_chart_path=AMPHORA_RELATIVE_CHART_PATH,
                       report_path=REPORT_PATH,
                       metrics=CADVISOR_METRIC_NAMES,
                       service="amphora",
                       request_name="createSecret")

# Create cAdvisor report for amphora getSecret request
generate_markdown_file(simulation_groups_promQL=AMPHORA_SIMULATION_GET_SECRET_GROUPS,
                       report_chart_path=AMPHORA_RELATIVE_CHART_PATH,
                       report_path=REPORT_PATH,
                       metrics=CADVISOR_METRIC_NAMES,
                       service="amphora",
                       request_name="getSecret")

# Create cAdvisor report for amphora deleteSecret request
generate_markdown_file(simulation_groups_promQL=AMPHORA_SIMULATION_DELETE_SECRET_GROUPS,
                       report_chart_path=AMPHORA_RELATIVE_CHART_PATH,
                       report_path=REPORT_PATH,
                       metrics=CADVISOR_METRIC_NAMES,
                       service="amphora",
                       request_name="deleteSecret")

# Create cAdvisor report for castor createSecret request
generate_markdown_file(simulation_groups_promQL=AMPHORA_SIMULATION_CREATE_SECRET_GROUPS,
                       report_chart_path=AMPHORA_RELATIVE_CHART_PATH,
                       report_path=REPORT_PATH,
                       metrics=CADVISOR_METRIC_NAMES,
                       service="castor",
                       request_name="createSecret")

# Create cAdvisor report for castor getSecret request
generate_markdown_file(simulation_groups_promQL=AMPHORA_SIMULATION_GET_SECRET_GROUPS,
                       report_chart_path=AMPHORA_RELATIVE_CHART_PATH,
                       report_path=REPORT_PATH,
                       metrics=CADVISOR_METRIC_NAMES,
                       service="castor",
                       request_name="getSecret")

# Create cAdvisor report for castor deleteSecret request
generate_markdown_file(simulation_groups_promQL=AMPHORA_SIMULATION_DELETE_SECRET_GROUPS,
                       report_chart_path=AMPHORA_RELATIVE_CHART_PATH,
                       report_path=REPORT_PATH,
                       metrics=CADVISOR_METRIC_NAMES,
                       service="castor",
                       request_name="deleteSecret")

# Create cAdvisor report for ephemeral execute request
generate_markdown_file(simulation_groups_promQL=EPHEMERAL_SIMULATION_GROUPS,
                       report_chart_path=EPHEMERAL_RELATIVE_CHART_PATH,
                       report_path=REPORT_PATH,
                       metrics=CADVISOR_METRIC_NAMES,
                       service="ephemeral",
                       request_name="execute")

# Create cAdvisor report for castor execute request
generate_markdown_file(simulation_groups_promQL=EPHEMERAL_SIMULATION_GROUPS,
                       report_chart_path=EPHEMERAL_RELATIVE_CHART_PATH,
                       report_path=REPORT_PATH,
                       metrics=CADVISOR_METRIC_NAMES,
                       service="castor",
                       request_name="execute")
