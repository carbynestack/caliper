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
EPHEMERAL_CHART_PATH = os.path.join(HOME_DIR, config['mkdocs']['charts']['ephemeral_simulation'])
REPORT_PATH = os.path.join(HOME_DIR, config['mkdocs']['report'])

AMPHORA_SIMULATION_CREATE_SECRET_GROUPS = config['simulation']['groups']['amphora']['createSecret']
AMPHORA_SIMULATION_GET_SECRET_GROUPS = config['simulation']['groups']['amphora']['getSecret']
AMPHORA_SIMULATION_DELETE_SECRET_GROUPS = config['simulation']['groups']['amphora']['deleteSecret']
EPHEMERAL_SIMULATION_EXECUTE_GROUPS = config['simulation']['groups']['ephemeral']['execute']


def generate_response_times_file(chart_file, data):
    """
    Generates markdown content with chapters and a table.

    :param chart_file: The file path of the chart.
    :param data: Table data including headers.
    """
    markdown_content = "# Gatling\n\n"
    markdown_content += "## Response Times\n\n"
    markdown_content += f"![Graph]({chart_file})\n\n"
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


for promQL, request in [(AMPHORA_SIMULATION_CREATE_SECRET_GROUPS, "createSecret"),
                        (AMPHORA_SIMULATION_GET_SECRET_GROUPS, "getSecret"),
                        (AMPHORA_SIMULATION_DELETE_SECRET_GROUPS, "deleteSecret"),
                        (EPHEMERAL_SIMULATION_EXECUTE_GROUPS, "execute")]:

    apollo_gatling_metrics_dict = APOLLO_PROMETHEUS_CLIENT.custom_query_range(
        query=promQL,
        start_time=START_TIME,
        end_time=END_TIME, step='15s')

    if len(apollo_gatling_metrics_dict) > 0:
        apollo_gatling_metrics_df = MetricRangeDataFrame(apollo_gatling_metrics_dict)
        # gatling sends the same metric in a configured interval, e.g. 1min
        apollo_gatling_metrics_df = apollo_gatling_metrics_df.drop_duplicates()
        apollo_gatling_metrics_df["timestamp"] = apollo_gatling_metrics_df.index

    service = "ephemeral" if request == "execute" else "amphora"

    try:
        plt.figure(figsize=(12, 7))

        colors = plt.cm.jet(np.linspace(0, 1, len(apollo_gatling_metrics_df)))

        for counter, (i, row) in enumerate(apollo_gatling_metrics_df.iterrows()):
            plt.scatter([row['timestamp']], [row['value']], color=colors[counter], label=row['group'])

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
        plt.legend(loc='best')
        # adjust padding
        plt.subplots_adjust(left=0.1)

        # Save the chart to the specified path
        file_name = f"{service}_{request}_response_times"
        chart_path = os.path.join(AMPHORA_CHART_PATH, service, file_name)
        plt.savefig(chart_path)
        plt.close()

        response_times_statistics = apollo_gatling_metrics_df.groupby('group')['value'].agg(
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

        # Save response time file to specified path
        filename = f"{REPORT_PATH}/{service}/{request}/{request}_response_times.md"
        chart_path = f"{chart_path}.png"
        markdown = generate_response_times_file(chart_path, data)
        with open(filename, 'w') as file:
            file.write(markdown)

        logger.info(f"Generated {filename}")

    except Exception as e:
        logger.error(e)
