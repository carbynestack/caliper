/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.action

import io.gatling.core.action.Action
import io.gatling.core.action.builder.ActionBuilder
import io.gatling.core.session.Session
import io.gatling.core.structure.ScenarioContext
import org.gatling.plugin.carbynestack.protocol.CsProtocol
import org.gatling.plugin.carbynestack.request.client.ProtocolBuilder

class CsActionBuilder[C, R](protocolBuilder: ProtocolBuilder[C], requestFunction: (C, Session) => R)
    extends ActionBuilder {

  override def build(ctx: ScenarioContext, next: Action): Action = {
    val csComponents = ctx.protocolComponentsRegistry.components(CsProtocol.CsProtocolKey)
    val coreComponents = ctx.coreComponents

    new CsAction(protocolBuilder, requestFunction, csComponents, coreComponents, next)
  }
}
