/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.request.client

import io.carbynestack.amphora.client.{AmphoraClient, DefaultAmphoraClient}
import io.carbynestack.amphora.common.AmphoraServiceUri
import org.gatling.plugin.carbynestack.protocol.CsComponents

import scala.jdk.CollectionConverters._

class AmphoraClientBuilder extends ClientBuilder[AmphoraClient] {

  override def build(csComponents: CsComponents): AmphoraClient = {
    DefaultAmphoraClient
      .builder()
      .endpoints(csComponents.protocol.amphoraEndpoints.map(uri => new AmphoraServiceUri(uri)).asJava)
      .prime(new java.math.BigInteger(csComponents.protocol.prime))
      .r(new java.math.BigInteger(csComponents.protocol.r))
      .rInv(new java.math.BigInteger(csComponents.protocol.invR))
      .build()
  }
}
