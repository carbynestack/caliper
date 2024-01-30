import logging.config
import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import yaml
from matplotlib import pyplot as plt, ticker
from prometheus_api_client import PrometheusConnect, MetricRangeDataFrame

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('generate_gatling_charts')

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

AMPHORA_CHART_PATH = os.path.join(HOME_DIR, config['mkdocs']['charts']['amphora_simulation'])
AMPHORA_RELATIVE_CHART_PATH = config['mkdocs']['report']['charts']['amphora_simulation']
EPHEMERAL_CHART_PATH = os.path.join(HOME_DIR, config['mkdocs']['charts']['ephemeral_simulation'])
EPHEMERAL_RELATIVE_CHART_PATH = config['mkdocs']['report']['charts']['ephemeral_simulation']
REPORT_PATH = os.path.join(HOME_DIR, config['mkdocs']['report']['services'])

AMPHORA_SIMULATION_CREATE_SECRET_GROUPS = config['simulation']['groups']['amphora']['createSecret']
AMPHORA_SIMULATION_GET_SECRET_GROUPS = config['simulation']['groups']['amphora']['getSecret']
AMPHORA_SIMULATION_DELETE_SECRET_GROUPS = config['simulation']['groups']['amphora']['deleteSecret']
EPHEMERAL_SIMULATION_EXECUTE_GROUPS = config['simulation']['groups']['ephemeral']['execute']


def generate_markdown_file(simulation_groups_df, service, report_chart_path, chart_filename):
    """
    :param simulation_groups_df: simulation groups.
    :param service: Name of the service.
    :param report_chart_path: relative path to the response times chart.
    :param chart_filename: chart filename.
    """
    response_times_statistics = simulation_groups_df.groupby('group')['value'].agg(
        count='count',
        min='min',
        percentile_50=lambda x: x.quantile(0.5),
        percentile_75=lambda x: x.quantile(0.75),
        percentile_95=lambda x: x.quantile(0.95),
        percentile_99=lambda x: x.quantile(0.99),
        max='max',
        mean='mean',
        std_dev='std'
    ).map(lambda x: int(x) if pd.notnull(x) else x)

    # Convert DataFrame to list of lists
    data = [['group'] + list(response_times_statistics.columns)]  # Header
    data += response_times_statistics.reset_index().values.tolist()  # Data rows

    markdown_content = "# Gatling\n\n"
    markdown_content += "## Response Times\n\n"
    markdown_content += f"![Graph]({report_chart_path}/{service}/{chart_filename})\n\n"
    markdown_content += "## Summary\n\n"

    # Calculate max length for each column
    max_lengths = [max(len(str(row[i])) for row in data) for i in range(len(data[0]))]

    # Add header
    header = data[0]
    markdown_content += "| " + " | ".join(header) + " |\n"

    # Add separator
    separator = ["-" * (max_lengths[i] + 2) for i in range(len(header))]
    markdown_content += "|" + "|".join(separator) + "|\n"

    # Add rows
    for row in data[1:]:
        row_formatted = [str(row[i]).ljust(max_lengths[i]) for i in range(len(row))]
        markdown_content += "| " + " | ".join(row_formatted) + " |\n"

    return markdown_content


def generate_report_file(simulation_groups_promQL, request_name, service, chart_path, report_path, report_chart_path):
    """
    :param simulation_groups_promQL: query to retrieve simulation groups.
    :param request_name: request executed in the simulation group.
    :param service: Name of the service.
    :param chart_path: path to the charts location.
    :param report_path: path to the report location.
    :param report_chart_path: relative path to the response times chart.
    """
    simulation_groups_dict = APOLLO_PROMETHEUS_CLIENT.custom_query_range(
        query=simulation_groups_promQL,
        start_time=START_TIME,
        end_time=END_TIME, step='15s')

    if len(simulation_groups_dict) > 0:
        simulation_groups_df = MetricRangeDataFrame(simulation_groups_dict)
        # gatling sends the same metric in a configured interval, e.g. 1min
        simulation_groups_df = simulation_groups_df.drop_duplicates()
        simulation_groups_df["timestamp"] = simulation_groups_df.index

        try:
            plt.figure(figsize=(12, 7))

            colors = plt.cm.jet(np.linspace(0, 1, len(simulation_groups_df)))

            for counter, (i, row) in enumerate(simulation_groups_df.iterrows()):
                plt.scatter([row['timestamp']], [row['value']], color=colors[counter])

            # Adding grid
            plt.grid(True, which='both', linestyle='--', linewidth=0.5)

            # Hiding the top and right spines
            ax = plt.gca()  # Get the current Axes instance
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            # Set ticks direction to inward
            ax.tick_params(axis='both', which='both', direction='in')

            # Formatting the plot
            plt.tight_layout()
            plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
            plt.gca().xaxis.set_major_locator(plt.MaxNLocator(12))
            plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda value, pos: (
                f'{value / 1e3:.2f} s' if value >= 1e3 else
                f'{value:.0f} ms'
            )))
            # adjust padding
            plt.subplots_adjust(left=0.1)

            # Save the chart to the specified path
            chart_filename = f"{service}_{request_name}_response_times"
            chart_path = os.path.join(chart_path, service, chart_filename)
            plt.savefig(chart_path)
            plt.close()

            logger.info(f"Generated {chart_filename}")

            # Generate markdown content
            markdown_content = generate_markdown_file(simulation_groups_df=simulation_groups_df,
                                                      service=service,
                                                      report_chart_path=report_chart_path,
                                                      chart_filename=f"{chart_filename}.png")

            # Save response time file to specified path
            report_filename = f"{report_path}/{service}/{request_name}/{request_name}_response_times.md"
            with open(report_filename, 'w') as file:
                file.write(markdown_content)

                logger.info(f"Generated {report_filename}")
        except Exception as e:
            logger.error(
                f"Error: {e} for service: {service} and request: {request_name} and groups: {simulation_groups_promQL}")
    else:
        logger.error(f"No simulation groups found for service: {service} and query: {simulation_groups_promQL}")


# Create response times report for amphorasimulation createSecret request
generate_report_file(simulation_groups_promQL=AMPHORA_SIMULATION_CREATE_SECRET_GROUPS,
                     request_name="createSecret",
                     service="amphora",
                     chart_path=AMPHORA_CHART_PATH,
                     report_path=REPORT_PATH,
                     report_chart_path=AMPHORA_RELATIVE_CHART_PATH)

# Create response times report for amphorasimulation getSecret request
generate_report_file(simulation_groups_promQL=AMPHORA_SIMULATION_GET_SECRET_GROUPS,
                     request_name="getSecret",
                     service="amphora",
                     chart_path=AMPHORA_CHART_PATH,
                     report_path=REPORT_PATH,
                     report_chart_path=AMPHORA_RELATIVE_CHART_PATH)

# Create response times report for amphorasimulation deleteSecret request
generate_report_file(simulation_groups_promQL=AMPHORA_SIMULATION_DELETE_SECRET_GROUPS,
                     request_name="deleteSecret",
                     service="amphora",
                     chart_path=AMPHORA_CHART_PATH,
                     report_path=REPORT_PATH,
                     report_chart_path=AMPHORA_RELATIVE_CHART_PATH)

# Create response times report for ephemeralsimulation execute request
generate_report_file(simulation_groups_promQL=EPHEMERAL_SIMULATION_EXECUTE_GROUPS,
                     request_name="execute",
                     service="ephemeral",
                     chart_path=EPHEMERAL_CHART_PATH,
                     report_path=REPORT_PATH,
                     report_chart_path=EPHEMERAL_RELATIVE_CHART_PATH)
