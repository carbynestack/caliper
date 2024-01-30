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

AMPHORA_CHART_PATH = os.path.join(HOME_DIR, config['mkdocs']['charts']['amphora_simulation'])
EPHEMERAL_CHART_PATH = os.path.join(HOME_DIR, config['mkdocs']['charts']['ephemeral_simulation'])
REPORT_PATH = os.path.join(HOME_DIR, config['mkdocs']['report'])

AMPHORA_SIMULATION_CREATE_SECRET_GROUPS = config['simulation']['groups']['amphora']['createSecret']
AMPHORA_SIMULATION_GET_SECRET_GROUPS = config['simulation']['groups']['amphora']['getSecret']
AMPHORA_SIMULATION_DELETE_SECRET_GROUPS = config['simulation']['groups']['amphora']['deleteSecret']
EPHEMERAL_SIMULATION_GROUPS = config['simulation']['groups']['ephemeral']['execute']


def generate_markdown_file(chart_path, report_path, metrics, service, group, request):
    """
    Generates a cAdvisor metrics markdown file for the report.

    :param chart_path: path to the chart directory.
    :param report_path: path to the report directory.
    :param metrics: cAdvisor metrics.
    :param service: name of the service.
    :param group: gatling group.
    :param request: Carbyne Stack client request.
    """
    markdown_content = "# cAdvisor\n\n"

    for metric in metrics:
        chart_file = f"{chart_path}/{service}/{service}_{group}_{metric}.png"

        if os.path.exists(chart_file):
            markdown_content += f"## {metric}\n\n![Graph]({chart_file})\n\n"
        else:
            logger.error(f"Chart {chart_file} not found")
            continue

        report_directory = f"{report_path}/{service}/{request}"
        os.makedirs(report_directory, exist_ok=True)
        filename = f"{report_directory}/{group}.md"

        try:
            with open(filename, 'w') as file:
                file.write(markdown_content)
            logger.info(f"Generated {filename}")
        except Exception as e:
            logger.error(f"Error writing to {filename}: {e}")


for promQL, request in [(AMPHORA_SIMULATION_CREATE_SECRET_GROUPS, "createSecret"),
                        (AMPHORA_SIMULATION_GET_SECRET_GROUPS, "getSecret"),
                        (AMPHORA_SIMULATION_DELETE_SECRET_GROUPS, "deleteSecret"),
                        (EPHEMERAL_SIMULATION_GROUPS, "execute")]:

    apollo_gatling_metrics_dict = APOLLO_PROMETHEUS_CLIENT.custom_query_range(
        query=promQL,
        start_time=START_TIME,
        end_time=END_TIME, step='15s')

    if len(apollo_gatling_metrics_dict) > 0:
        apollo_gatling_metrics_df = MetricRangeDataFrame(apollo_gatling_metrics_dict)
        # gatling sends the same metric in a configured interval, e.g. 1min
        apollo_gatling_metrics_df = apollo_gatling_metrics_df.drop_duplicates()

    try:
        # TODO temporär
        groups = apollo_gatling_metrics_df['group'].drop_duplicates()

        services = ["ephemeral", "castor"] if request == "execute" else ["amphora", "castor"]
        for service in services:
            for group in groups:
                generate_markdown_file(
                    chart_path=AMPHORA_CHART_PATH,
                    report_path=REPORT_PATH,
                    metrics=CADVISOR_METRIC_NAMES,
                    service=service,
                    group=group,
                    request=request)
    except Exception as e:
        logger.error(e)
