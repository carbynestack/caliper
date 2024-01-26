# Caliper Report

## Test Environment

| Size           | vCPU | Memory (GiB) | Temp storage SSD (GiB) | Max temp storage throughput: IOPS/ Read MBps/ Write MBps | Max data disks | Throughput IOPS | Max NICs | Expected network bandwidth (Mbps) |
| -------------- | ---- | ------------ | ---------------------- | -------------------------------------------------------- | -------------- | --------------- | -------- | --------------------------------- |
| Standard_D3_v2 | 4    | 14           | 200                    | 12000/187/93                                             | 16             | 16x500          | 4        | 3000                              |

_DSv2-series_ sizes run on the
`3rd Generation Intel® Xeon® Platinum 8370C (Ice Lake)`,
`Intel® Xeon® Platinum 8272CL (Cascade Lake)`,
`Intel® Xeon® 8171M 2.1GHz (Skylake)`, or the
`Intel® Xeon® E5-2673 v4 2.3 GHz (Broadwell)`, or the
`Intel® Xeon® E5-2673 v3 2.4 GHz (Haswell)` processors with Intel Turbo Boost
Technology 2.0 and use premium storage.

### Resource reservations

Allocatable resources are less than total resources since AKS uses node
resources to maintain node performance and functionality (see
[resource reservations](https://learn.microsoft.com/en-us/azure/aks/concepts-clusters-workloads)).

## Amphora

| Name                             | Objective                                                             | Users           | Description                                                                                      | Test data                        |
| -------------------------------- | --------------------------------------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------ | -------------------------------- |
| create_values_10000              | Evaluate performance when uploading secrets with small secret size    | 1 Virtual User  | Upload the secret                                                                                | fixed secret size, fixed tags    |
| create_values_50000              | Evaluate performance when uploading secrets with larger secret size   | 1 Virtual User  | Upload the secret                                                                                | fixed secret size, fixed tags    |
| create_values_50000_under_load   | Evaluate performance when uploading secrets when system is under load | 1 Virtual User  | Upload the secret after 1.000.000 secrets were uploaded                                          | fixed secret size, fixed tags    |
| createSecret_getSecrets_parallel | Evaluate performance during concurrent operations                     | 10 Virtual User | Secrets are uploaded by 5 users concurrently, and parallel 5 users download secrets concurrently | variable secret size, fixed tags |
| getSecret_10000                  | Evaluate performance when downloading secrets with small secret size  | 1 Virtual User  | Download all secrets                                                                             | fixed secret size, fixed tags    |
| getSecret_61000                  | Evaluate performance when downloading secrets with larger secret size | 1 Virtual User  | Download all secrets                                                                             | fixed secret size, fixed tags    |
| getSecret_161000                 | Evaluate performance when downloading secrets with large secret size  | 1 Virtual User  | Download all secrets                                                                             | fixed secret size, fixed tags    |

## Castor

_Castor_ offers no _Client Interface_, therefore cAdvisor metrics for _Castor_
are collected during the execution of _Amphora_ and _Ephemeral_ scenario(s). For
each group the corresponding charts are created.

## Ephemeral

| Name                           | Objective                                                   | Users           | Description                                                    | Test data                        |
| ------------------------------ | ----------------------------------------------------------- | --------------- | -------------------------------------------------------------- | -------------------------------- |
| emptyProgram                   | Evaluate performance without expansive operation            | 1 Virtual User  | Upload the secrets, perform no operation on the input data     | fixed secret size, fixed tags    |
| scalarValueOptProgram          | Evaluate performance with expansive operation on input data | 1 Virtual User  | Upload the secrets, execute the program                        | variable secret size, fixed tags |
| scalarValueOptProgram_parallel | Evaluate performance with concurrent program execution      | 10 Virtual User | Upload the secrets, execute program with 10 users concurrently | fixed secret size, fixed tags    |
