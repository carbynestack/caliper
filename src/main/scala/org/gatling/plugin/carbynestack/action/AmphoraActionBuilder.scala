package org.gatling.plugin.carbynestack.action

import io.carbynestack.amphora.client.AmphoraClient
import io.gatling.core.action.Action
import io.gatling.core.action.builder.ActionBuilder
import io.gatling.core.session.Session
import io.gatling.core.structure.ScenarioContext
import org.gatling.plugin.carbynestack.protocol.CsProtocol
import org.gatling.plugin.carbynestack.request.client.AmphoraClientBuilder

class AmphoraActionBuilder[R](
  clientBuilder: AmphoraClientBuilder,
  requestFunction: (AmphoraClient, Session) => R
) extends ActionBuilder {
  override def build(ctx: ScenarioContext, next: Action): Action = {

    val csComponents = ctx.protocolComponentsRegistry.components(CsProtocol.CsProtocolKey)
    val coreComponents = ctx.coreComponents

    new AmphoraAction[R](clientBuilder.build(csComponents), requestFunction, coreComponents, next)
  }
}
