/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.util

import io.carbynestack.amphora.client.Secret

import java.math.BigInteger
import scala.util.Random

class SecretGenerator(
  val tagGenerator: TagGenerator,
  val lowerBound: Long,
  val upperBound: Long,
  val numberOfSecrets: Int
) {

  def generate: Secret = {
    val tags = tagGenerator.generate
    val secrets =
      Array.fill[BigInteger](numberOfSecrets)(
        new BigInteger((lowerBound + Random.nextLong(upperBound - lowerBound)).toString)
      )
    Secret.of(tags, secrets)
  }
}
