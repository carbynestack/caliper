/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack

import org.gatling.plugin.carbynestack.protocol.CsProtocolBuilder
import org.gatling.plugin.carbynestack.request.builder.{Amphora, Ephemeral}

trait CsDsl {

  def cs: CsProtocolBuilder = CsProtocolBuilder()

  def amphora: Amphora = new Amphora()

  def ephemeral: Ephemeral = new Ephemeral()
}
