import logging.config
import os
from datetime import datetime, timedelta, timezone

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import yaml
from prometheus_api_client import PrometheusConnect, MetricRangeDataFrame

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('generate_cAdvisor_charts')

# config file
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

APOLLO_NODE_IP = os.environ['APOLLO_NODE_IP']
STARBUCK_NODE_IP = os.environ['STARBUCK_NODE_IP']
PROMETHEUS_SERVER_PORT = os.environ['PROMETHEUS_SERVER_PORT']

APOLLO_PROMETHEUS_CLIENT = PrometheusConnect(url=f"http://{APOLLO_NODE_IP}:{PROMETHEUS_SERVER_PORT}",
                                             disable_ssl=True)
STARBUCK_PROMETHEUS_CLIENT = PrometheusConnect(url=f"http://{STARBUCK_NODE_IP}:{PROMETHEUS_SERVER_PORT}",
                                               disable_ssl=True)

HOME_DIR = os.environ['HOME']

END_TIME = datetime.now(timezone.utc)  # Prometheus uses UTC
START_TIME = END_TIME - timedelta(hours=config['simulation']['time_delta'])

CADVISOR_METRICS = config['cAdvisor']['container']['metric_names']
CADVISOR_METRICS_TEMPLATE = config['cAdvisor']['container']['metric_templates']

AMPHORA_CHART_PATH = os.path.join(HOME_DIR, config['mkdocs']['charts']['amphora_simulation'])
EPHEMERAL_CHART_PATH = os.path.join(HOME_DIR, config['mkdocs']['charts']['ephemeral_simulation'])

EPHEMERAL_SIMULATION_GROUPS = config['simulation']['ok']['ephemeral']
AMPHORA_SIMULATION_GROUPS = config['simulation']['ok']['amphora']


def generate_cAdvisor_metrics(container, pod):
    all_metrics = []

    metric = [metric_query.format(container=container, pod=pod)
              for metric_query in CADVISOR_METRICS_TEMPLATE]
    all_metrics.extend(metric)

    return all_metrics


AMPHORA_CADVISOR_METRICS = generate_cAdvisor_metrics(container="amphora", pod="cs-amphora")
CASTOR_CADVISOR_METRICS = generate_cAdvisor_metrics(container="castor", pod="cs-castor")
EPHEMERAL_CADVISOR_METRICS = generate_cAdvisor_metrics(container="ephemeral-ephemeral", pod="ephemeral")

amphora_simulation_groups_dict = APOLLO_PROMETHEUS_CLIENT.custom_query_range(query=AMPHORA_SIMULATION_GROUPS,
                                                                             start_time=START_TIME,
                                                                             end_time=END_TIME, step='15s')

ephemeral_simulation_groups_dict = APOLLO_PROMETHEUS_CLIENT.custom_query_range(query=EPHEMERAL_SIMULATION_GROUPS,
                                                                               start_time=START_TIME,
                                                                               end_time=END_TIME, step='15s')
# Time ranges per group
if len(amphora_simulation_groups_dict) > 0:
    amphora_simulation_groups_df = MetricRangeDataFrame(amphora_simulation_groups_dict)
    # gatling sends the same metric in a configured interval, e.g. 1min
    amphora_simulation_groups_df = amphora_simulation_groups_df.drop_duplicates()
    amphora_simulation_groups_df["timestamp"] = amphora_simulation_groups_df.index

    amphora_simulation_groups_start_times = amphora_simulation_groups_df.groupby("group")['timestamp'].min()
    amphora_simulation_groups_end_times = amphora_simulation_groups_df.groupby("group")['timestamp'].max()

if len(ephemeral_simulation_groups_dict) > 0:
    ephemeral_simulation_groups_df = MetricRangeDataFrame(ephemeral_simulation_groups_dict)
    # gatling sends the same metric in a configured interval, e.g. 1min
    ephemeral_simulation_groups_df = ephemeral_simulation_groups_df.drop_duplicates()
    ephemeral_simulation_groups_df["timestamp"] = amphora_simulation_groups_df.index

    ephemeral_simulation_groups_start_times = ephemeral_simulation_groups_df.groupby("group")['timestamp'].min()
    ephemeral_simulation_groups_end_times = ephemeral_simulation_groups_df.groupby("group")['timestamp'].max()


def generate_cAdvisor_charts(groups, cadvisor_metrics_names, cadvisor_metrics_promQL, simulation_groups_start_times,
                             simulation_groups_end_times, chart_path, service):
    """
    Generates charts for specified groups and metrics.

    :param groups: Series containing group names.
    :param cadvisor_metrics_names: List with metric names.
    :param cadvisor_metrics_promQL: List with corresponding PromQL queries.
    :param simulation_groups_start_times: start times per group for a simulation.
    :param simulation_groups_end_times: end time per group for a simulation.
    :param chart_path: directory to store charts.
    :param service: Name of the service.
    """
    for group in groups:
        for metric_name, promQL in zip(cadvisor_metrics_names, cadvisor_metrics_promQL):
            apollo_cAdvisor_metrics_dict = APOLLO_PROMETHEUS_CLIENT.custom_query_range(query=promQL,
                                                                                       start_time=START_TIME,
                                                                                       end_time=END_TIME, step='15s')

            starbuck_cAdvisor_metrics_dict = STARBUCK_PROMETHEUS_CLIENT.custom_query_range(query=promQL,
                                                                                           start_time=START_TIME,
                                                                                           end_time=END_TIME,
                                                                                           step='15s')

            apollo_cAdvisor_metrics_df = MetricRangeDataFrame(apollo_cAdvisor_metrics_dict)
            starbuck_cAdvisor_metrics_df = MetricRangeDataFrame(starbuck_cAdvisor_metrics_dict)

            # Plotting the data
            plt.figure(figsize=(12, 7))

            # Get the relevant data per group per cluster
            for label, df in [('Apollo', apollo_cAdvisor_metrics_df), ('Starbuck', starbuck_cAdvisor_metrics_df)]:
                cAdvisor_metrics_df_sliced = df[
                    (df.index >= (
                            simulation_groups_start_times[group] - timedelta(minutes=2))) &
                    (df.index <= simulation_groups_end_times[group])]

                plt.plot(cAdvisor_metrics_df_sliced.index, cAdvisor_metrics_df_sliced['value'], label=label)

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
            if 'cpu' not in metric_name:
                plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda value, pos: (
                    f'{value / 1e9:.2f} GB' if value >= 1e9 else
                    f'{value / 1e6:.2f} MB' if value >= 1e6 else
                    f'{value / 1e3:.2f} KB' if value >= 1e3 else
                    f'{value:.0f}'
                )))
            plt.legend(loc='best')
            # adjust padding
            plt.subplots_adjust(left=0.1)

            # Save the chart to the specified path
            file_name = f"{service}_{group}_{metric_name}"
            file_path = os.path.join(chart_path, service, file_name)
            plt.savefig(file_path)
            plt.close()

            logger.info(f"Generated {file_path}")


try:
    # Create charts for amphora for amphorasimulation
    generate_cAdvisor_charts(groups=amphora_simulation_groups_df['group'],
                             cadvisor_metrics_names=CADVISOR_METRICS,
                             cadvisor_metrics_promQL=AMPHORA_CADVISOR_METRICS,
                             simulation_groups_start_times=amphora_simulation_groups_start_times,
                             simulation_groups_end_times=amphora_simulation_groups_end_times,
                             chart_path=AMPHORA_CHART_PATH,
                             service="amphora")

    # Create charts for castor for amphorasimulation
    generate_cAdvisor_charts(groups=amphora_simulation_groups_df['group'],
                             cadvisor_metrics_names=CADVISOR_METRICS,
                             cadvisor_metrics_promQL=CASTOR_CADVISOR_METRICS,
                             simulation_groups_start_times=amphora_simulation_groups_start_times,
                             simulation_groups_end_times=amphora_simulation_groups_end_times,
                             chart_path=AMPHORA_CHART_PATH,
                             service="castor")

    # Create charts for ephemeral for ephemeralsimulation
    generate_cAdvisor_charts(groups=ephemeral_simulation_groups_df['group'],
                             cadvisor_metrics_names=CADVISOR_METRICS,
                             cadvisor_metrics_promQL=EPHEMERAL_CADVISOR_METRICS,
                             simulation_groups_start_times=ephemeral_simulation_groups_start_times,
                             simulation_groups_end_times=ephemeral_simulation_groups_end_times,
                             chart_path=EPHEMERAL_CHART_PATH,
                             service="ephemeral")

    # Create charts for castor for ephemeralsimulation
    generate_cAdvisor_charts(groups=ephemeral_simulation_groups_df['group'],
                             cadvisor_metrics_names=CADVISOR_METRICS,
                             cadvisor_metrics_promQL=CASTOR_CADVISOR_METRICS,
                             simulation_groups_start_times=ephemeral_simulation_groups_start_times,
                             simulation_groups_end_times=ephemeral_simulation_groups_end_times,
                             chart_path=EPHEMERAL_CHART_PATH,
                             service="castor")
except Exception as e:
    logger.error(e)
