/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.protocol

import com.typesafe.scalalogging.StrictLogging
import io.gatling.core.CoreComponents
import io.gatling.core.config.GatlingConfiguration
import io.gatling.core.protocol.{Protocol, ProtocolKey}

object CsProtocol extends StrictLogging {

  val CsProtocolKey: ProtocolKey[CsProtocol, CsComponents] =
    new ProtocolKey[CsProtocol, CsComponents] {

      override def protocolClass: Class[Protocol] =
        classOf[CsProtocol].asInstanceOf[Class[Protocol]]

      override def defaultProtocolValue(configuration: GatlingConfiguration): CsProtocol =
        throw new IllegalStateException("Can't provide a default value for CsProtocol")

      override def newComponents(coreComponents: CoreComponents): CsProtocol => CsComponents = { csProtocol =>
        CsComponents(csProtocol)
      }
    }

  def apply(
    endpoints: List[String] = Nil,
    prime: String = null,
    r: String = null,
    invR: String = null,
  ): CsProtocol =
    new CsProtocol(endpoints, prime, r, invR)
}

case class CsProtocol(
  endpoints: List[String],
  prime: String,
  r: String,
  invR: String,
) extends Protocol {
  type Components = CsComponents
}
