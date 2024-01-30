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

| Name                         | Objective                     | Users          | Description                        | Test data                   |
| ---------------------------- | ----------------------------- | -------------- | ---------------------------------- | --------------------------- |
| createSecret_1000            | Evaluate upload performance   | 1 Virtual User | Upload the secret                  | fixed secret size, 100 tags |
| createSecret_10000           | Evaluate upload performance   | 1 Virtual User | Upload the secret                  | fixed secret size, 100 tags |
| createSecret_50000           | Evaluate upload performance   | 1 Virtual User | Upload the secret                  | fixed secret size, 100 tags |
| createSecret_100000          | Evaluate upload performance   | 1 Virtual User | Upload the secret                  | fixed secret size, 100 tags |
| createSecret_250000          | Evaluate upload performance   | 1 Virtual User | Upload the secret                  | fixed secret size, 100 tags |
| createSecret_400000          | Evaluate upload performance   | 1 Virtual User | Upload the secret                  | fixed secret size, 100 tags |
| createSecret_1000_repeat_10  | Evaluate upload performance   | 1 Virtual User | Upload the secret, repeat 10 times | fixed secret size, 100 tags |
| createSecret_10000_repeat_10 | Evaluate upload performance   | 1 Virtual User | Upload the secret, repeat 10 times | fixed secret size, 100 tags |
| createSecret_50000_repeat_10 | Evaluate upload performance   | 1 Virtual User | Upload the secret, repeat 10 times | fixed secret size, 100 tags |
| createSecret_100000_repeat_5 | Evaluate upload performance   | 1 Virtual User | Upload the secret, repeat 5 times  | fixed secret size, 100 tags |
| getSecret_1000               | Evaluate download performance | 1 Virtual User | Download the secret                | fixed secret size, 100 tags |
| getSecret_11000              | Evaluate download performance | 1 Virtual User | Download the secret                | fixed secret size, 100 tags |
| getSecret_61000              | Evaluate download performance | 1 Virtual User | Download the secret                | fixed secret size, 100 tags |
| getSecret_161000             | Evaluate download performance | 1 Virtual User | Download the secret                | fixed secret size, 100 tags |
| getSecret_261000             | Evaluate download performance | 1 Virtual User | Download the secret                | fixed secret size, 100 tags |
| deleteSecret_all             | Evaluate deletion performance | 1 Virtual User | Delete all secret                  | fixed secret size, 100 tags |

## Castor

_Castor_ offers no _Client Interface_, therefore cAdvisor metrics for _Castor_
are collected during the execution of _Amphora_ and _Ephemeral_ scenario(s). For
each group the corresponding charts are created.

## Ephemeral

| Name                  | Objective                                                   | Users          | Description                                                  | Test data                        |
| --------------------- | ----------------------------------------------------------- | -------------- | ------------------------------------------------------------ | -------------------------------- |
| emptyProgram          | Evaluate performance without expansive operation            | 1 Virtual User | Upload the secrets, perform no operation on the input data   | fixed secret size, fixed tags    |
| scalarValueOptProgram | Evaluate performance with expansive operation on input data | 1 Virtual User | Upload the secrets, perform multiplication on the input data | variable secret size, fixed tags |
