# Carbyne Stack Caliper Load Testing Harness

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/233198c332f3486ea69057fb9938917e)](https://app.codacy.com/gh/carbynestack/caliper/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Known Vulnerabilities](https://snyk.io/test/github/carbynestack/caliper/badge.svg)](https://snyk.io/test/github/carbynestack/caliper)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

> **DISCLAIMER**: Carbyne Stack Caliper is in *proof-of-concept* stage. The
> software is not ready for production use. It has neither been developed nor
> tested for a specific use case.

Caliper is the Load-Testing-as-Code harness for
[Carbyne Stack](https://github.com/carbynestack). This project is based on the
[Gatling](https://github.com/gatling/gatling) load test tool and provides a
plugin that can be used to communicate with backend services of a Carbyne Stack
Virtual Cloud using the dedicated java-clients.

## Components

### Protocol

The `cs` object is used to provide a common configuration that is shared between
all virtual users. A list of service endpoint URIs and the SPDZ parameters
matching the backend service configuration are used to initialize the clients.

### Action

To test the performance of one or multiple backend services of a
`Carbyne Stack Virtual Cloud` we create scenarios that make requests to a
backend service. The `exec` method is used to execute an
`io.gatling.core.action`, in the context of this plugin, actions are requests
performed by a client that will be sent during a simulation.

## Usage

To execute a simulation we can use the `gatling-maven-plugin`. Currently two
Carbyne Stack Clients (Amphora and Ephemeral) are supported, for each service we
create a collection of tests in a simulation class located under
`test/scala/simulation`. You can control which simulations will be triggered
with the `includes` filter.

```xml

<plugin>
    <groupId>io.gatling</groupId>
    <artifactId>gatling-maven-plugin</artifactId>
    <version>${maven-gatling-plugin.version}</version>
    <configuration>
        <runMultipleSimulations>true</runMultipleSimulations>
        <includes>
            <include>simulation.*</include>
        </includes>
    </configuration>
</plugin>
```

By default, the results are stored in `${project.build.directory}/gatling`.
Caliper uses [Prometheus](https://prometheus.io/) to visualize the results,
therefore all metrics are sent to a graphite endpoint configured in the
configuration file`test/resources/gatling.conf`. To run one or multiple
simulation classes simply use the `test` goal `./mvnw gatling:test`. The
following example shows a simulation class that provides the functionality of
the millionaires problem example from
[Carbyne Stack Tutorial](https://carbynestack.io/getting-started/millionaires/).

```scala
class CarbynestackSimulation extends Simulation { // 1

  val csProtocol = cs // 2
    .endpoints(List(apolloFqdn, starbuckFqdn))
    .prime("198766463529478683931867765928436695041")
    .r("141515903391459779531506841503331516415")
    .invR("133854242216446749056083838363708373830")
    .program("ephemeral-generic.default")

  val jeffTag: java.util.List[Tag] =
    List(("billionaire", "jeff"))
      .map(
        x =>
          Tag
            .builder()
            .key(x._1)
            .value(x._2)
            .valueType(TagValueType.STRING)
            .build()
      )
      .asJava

  val elonTag: java.util.List[Tag] =
    List(("billionaire", "elon"))
      .map(
        x =>
          Tag
            .builder()
            .key(x._1)
            .value(x._2)
            .valueType(TagValueType.STRING)
            .build()
      )
      .asJava

  val jeffSecret: Array[java.math.BigInteger] = Array(new java.math.BigInteger("180"))
  val elonSecret: Array[java.math.BigInteger] = Array(new java.math.BigInteger("177"))

  val jeffsNetWorth = Secret.of(jeffTag, jeffSecret)
  val elonsNetWorth = Secret.of(elonTag, elonSecret)

  val code =
    "port=regint(10000)\n" +
      "listen(port)\n" +
      "socket_id = regint()\n" +
      "acceptclientconnection(socket_id, port)\n" +
      "v = sint.read_from_socket(socket_id, 2)\n" +
      "first_billionaires_net_worth = v[0]\n" +
      "second_billionaires_net_worth= v[1]\n" +
      "result = first_billionaires_net_worth < second_billionaires_net_worth\n" +
      "resp = Array(1, sint)\n" +
      "resp[0] = result\n" +
      "sint.write_to_socket(socket_id, resp)"

  val jeffFeeder = Array(
    Map("secret" -> jeffsNetWorth)
  )

  val elonFeeder = Array(
    Map("secret" -> elonsNetWorth)
  )

  val millionairesProblem = scenario("millionaires-problem-scenario") // 3
    .feed(jeffFeeder) // 4
    .exec(amphora.createSecret("#{secret}")) // 5
    .feed(elonFeeder)
    .exec(amphora.createSecret("#{secret}"))
    .exec(amphora.getSecrets()) // 6
    .group("millionaires_problem_group") { // 7
      exec(ephemeral.execute(code, "#{uuids}")) // 8
    }

  setUp( // 9
    millionairesProblem.inject(atOnceUsers(1)) // 10
  ).protocols(csProtocol) // 11
}
```

1. The class declaration, it needs to extend `Simulation`.
1. The common configuration to all Carbyne Stack clients, see
   [amphora-java-client](https://github.com/carbynestack/amphora/blob/master/amphora-java-client/README.md).
1. The
   [Scenario](https://gatling.io/docs/gatling/reference/current/core/scenario/)
   definition.
1. A
   [Feeder](https://gatling.io/docs/gatling/reference/current/core/session/feeder/)
   is used to inject data into the virtual user. Essentially this is a hashmap
   with `"secret" -> io.carbynestack.amphora.client.Secret`.
1. An amphora-java-client-request calling the `createSecret` method of the
   `io.carbynestack.amphora.client.AmphoraClient`. Using the
   [Gatling Expression Language](https://gatling.io/docs/gatling/reference/current/core/session/el/)
   we can use dynamic parameters that will be replaced with the value stored in
   the virtual user's session.
1. An amphora-java-client-request that downloads all available secrets from the
   `VC` and stores them in the virtual user's session.
1. Gatling `groups` are used to divide a `scenario` into different test-cases,
   e.g. grouping requests with similar request-parameters.
1. An ephemeral-java-client-request executing the provided program, the secrets
   used by the program must be available in the virtual user's session under
   `"uuids" -> List[UUID]` and are used as input to the function.
1. Setting up the scenario(s) we want to use in this simulation.
1. Declaring that 1 virtual user will be injected into the `millionairesProblem`
   scenario.
1. Attaching the `cs` configuration matching the backend service configuration.

## Test Infrastructure

To run the load-tests a *Carbyne Stack Virtual Cloud* has to be deployed.
Caliper uses
[Infrastructure as Code](https://carbynestack.io/getting-started/deployment/infrastructure-as-code/)
to deploy a two-party VC hosted on *Microsoft Azure*. The following resources
are created by running the IaC deployment:

- *PrivateAksStack*: Deploys an AzureVM that is later peered with the Carbyne
  Stack VC.
- *PrivateAksVirtualCloudStack*: Deploys two private AKS cluster and a two-party
  Carbyne Stack VC.
- *GraphiteExporter*: Deploys an app to transform and expose metrics for
  Prometheus.
- *Prometheus*: Deploys a Prometheus server and config resources.

> **Important**: The following resources have to be created before running the
> deployment.

| Resource          | Name                             | Role                                                  | Usage                                                                                                          | Expiration |
| ----------------- | -------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------- |
| Managed Identity  | `caliper-aks-managed-identity`   | `Private DNS Zone Contributor`, `Network Contributor` | [Configure a private DNS zone](https://learn.microsoft.com/en-us/azure/aks/private-clusters?tabs=azure-portal) | -          |
| Service Principal | `caliper-test-infrastructure-sp` | `Contributer-Role`                                    | Authenticate Terraform to Azure                                                                                | 2/27/2024  |

## Report

*Caliper* creates a report that provides charts about resource consumption and
response times of the deployed services. To visualize the data, the *Matplotlib*
library is used in python scripts located under `/scripts/python`. The following
data sources are used to create the report:

### cAdvisor

[cAdvisor](https://github.com/google/cadvisor) is a running daemon that
collects, aggregates, processes, and exports information about running
containers. The following metrics are currently added to the report:

| Metric Name                              | Type    | Description                           | Unit    | Option parameter |
| ---------------------------------------- | ------- | ------------------------------------- | ------- | ---------------- |
| `container_memory_working_set_bytes`     | Gauge   | Current working set                   | bytes   | memory           |
| `container_cpu_usage_seconds_total`      | Counter | Cumulative cpu time consumed          | seconds | cpu              |
| `container_fs_writes_bytes_total`        | Counter | Cumulative count of bytes written     | bytes   | diskIO           |
| `container_fs_reads_bytes_total`         | Counter | Cumulative count of bytes read        | bytes   | diskIO           |
| `container_network_receive_bytes_total`  | Counter | Cumulative count of bytes received    | bytes   | network          |
| `container_network_transmit_bytes_total` | Counter | Cumulative count of bytes transmitted | bytes   | network          |

### Gatling

*Gatling* can export
[metrics](https://gatling.io/docs/gatling/guides/realtime_monitoring) over the
`Graphite plaintext` protocol. For this, `graphite` must be added to the data
writers and a target host, which in this context is the
[GraphiteExporter](https://github.com/prometheus/graphite_exporter), has to be
specified:

```text
 graphite {
      #light = false
      host = "10.1.1.5"           # Apollo node IP
      port = 32766                # GraphiteExporter
      protocol = "tcp"
      rootPathPrefix = "gatling"
      bufferSize = 8192
      writePeriod = 60
    }
```

### Generate Charts

Prometheus provides metrics in the format
`<metric name>{<label name>=<label value>, ...}`, and the *GraphiteExporter*
sends the following metrics to the Prometheus Server:
`caliper{simulation=<SimulationClass>, group=<ScenarioGroup>,`
`metric=<GatlingMetric>, scope=<OK|KO|ALL>}`.

An example *Prometheus-PromQL* to retrieve all groups related to uploading
secrets to the *Virtual Cloud* might look like this:
`caliper{simulation="amphorasimulation", group=~"createSecret_.*",`
`metric="percentiles99", scope="ok"}`.

The Python scripts use these metrics to extract the start and end times for each
group in order to slice the cAdvisor charts accordingly, and to extract response
times for each group.

To host the report on a *MkDocs* site, the Charts are stored under
`mkdocs/docs/images/charts/{amphorasimulation|ephemeralsimulation}/{amphora|Castor|ephemeral}/{filename}.png`,
where `filename` has the format
`{amphora|castor|ephemeral}_{group}_{metric}.png`.

The report files are stored under
`mkdocs/docs/report/{service}/{request}/{group}.md`.

## GitHub Actions Workflow

A GitHub Actions Workflow `.github/workflows/caliper-load-tests.yaml` is used to
automatically *deploy a two party VC*, run the specified *test-cases* and
finally deploy a new version of the *report*.

- *Provision AzureVM*: Deploys an AzureVM.
- *Run Load-Tests*: Connects to the deployed AzureVM via SSH and runs a
  *setup-script* located under `scripts/run_caliper_load_tests.sh`.
- *Deploy latest Report*: pushes the latest report tagged with the current date
  to the `gh-pages` branch.
- *destroy*: Deletes the Azure resource group 'caliper-rg' to ensure that in
  case steps fail, all deployed resources are destroyed.

> **Important**: GitHub Pages needs to be enabled for the Caliper repository,
> with the branch the site is build from being set to `gh-pages` from the
> `/root` folder.

To provide versioning, the [mike](http:/google.com) plugin is used. Each time
the workflow is triggered, *Mike* uploads the latest report to the `gh-pages`
branch.

> **Important**: The following secrets must be available to run the GitHub
> Actions Workflow:

| Secret                  | Description                                    | Expiration |
| ----------------------- | ---------------------------------------------- | ---------- |
| `AZURE_SUBSCRIPTION_ID` | Authenticate Terraform to Azure                | -          |
| `AZURE_CLIENT_SECRET`   | Authenticate Terraform to Azure                | 2/27/2024  |
| `AZURE_TENANT_ID`       | Authenticate Terraform to Azure                | -          |
| `AZURE_CLIENT_ID`       | Authenticate Terraform to Azure                | -          |
| `CALIPER_PAT`           | Authenticate to Carbyne Stack Github Packages  | DATE       |
| `CALIPER_PRIVATE_KEY`   | SSH keypair private key                        | -          |
| `CALIPER_PUBLIC_KEY`    | SSH keypair public key                         | -          |
| `AZURE_CREDENTIALS`     | Login to Azure with a Service Principal Secret | -          |

> **NOTE**: See
> [Azure login](https://github.com/Azure/login?tab=readme-ov-file#login-with-a-service-principal-secret)
> for the AZURE_CREDENTIALS value.

The value for AZURE_CREDENTIALS has the format:

```json
{
    "clientSecret":  "******",
    "subscriptionId":  "******",
    "tenantId":  "******",
    "clientId":  "******"
}
```

> **NOTE**: See [Setting up a SSH Key](https://github.com/appleboy/ssh-action)
> for creating the SSH Keys.

## Add/ Remove Test-cases

To add test-cases, the following steps must be performed:

A *Simulation class* contains multiple *scenarios*,

1. Define a scenario which contains one or multiple *groups*: The scenario name
   is not relevant and only used for logical separation. A group combines one or
   multiple requests for which the *response times* and *cAdvisor charts* are
   generated.
1. The groups are named using the format `{request}_{test_objective}`, e.g. a
   group containing tests for uploading secrets with 1000 secret-values might be
   named `createSecret_1000`.
1. Add a test description to `mkdocs/docs/index.md` and update
   `mkdocs/config/nav.yaml` to include the test-cases.

## Namesake

> A *caliper* \[...\] is a device used to measure the dimensions of an object
> ([Source](https://en.wikipedia.org/wiki/Calipers)).

The object being measured in our case is Carbyne Stack. The dimensions are
primarily performance and scalability.

## License

The Carbyne Stack *Caliper Load-Testing-as-Code harness* is open-sourced under
the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

### 3rd Party Licenses

For information on how license obligations for 3rd party OSS dependencies are
fulfilled see the [README](https://github.com/carbynestack/carbynestack) file of
the Carbyne Stack repository.

## Contributing

Please see the Carbyne Stack
[Contributor's Guide](https://github.com/carbynestack/carbynestack/blob/master/CONTRIBUTING.md)
