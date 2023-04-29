/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.action

import io.gatling.commons.stats.{KO, OK}
import io.gatling.core.CoreComponents
import io.gatling.core.action.Action
import io.gatling.core.session.Session
import io.gatling.core.util.NameGen
import org.gatling.plugin.carbynestack.protocol.CsComponents
import org.gatling.plugin.carbynestack.request.client.ProtocolBuilder

class CsAction[C, R](
  protocolBuilder: ProtocolBuilder[C],
  function: (C, Session) => R,
  csComponents: CsComponents,
  coreComponents: CoreComponents,
  val next: Action
) extends Action
    with NameGen {

  override def name: String = genName("BaseRequest")

  override def execute(session: Session): Unit = {

    val client = protocolBuilder.build(csComponents)
    val start = coreComponents.clock.nowMillis
    try {

      function(client, session)

      coreComponents.statsEngine.logResponse(
        session.scenario,
        session.groups,
        session.scenario,
        start,
        coreComponents.clock.nowMillis,
        OK,
        None,
        None
      )
    } catch {
      case e: Throwable =>
        logger.error(e.getMessage, e)
        coreComponents.statsEngine.logResponse(
          session.scenario,
          session.groups,
          session.scenario,
          start,
          coreComponents.clock.nowMillis,
          KO,
          Some("500"),
          Some(e.getMessage),
        )
    }
    next ! session
  }
}
