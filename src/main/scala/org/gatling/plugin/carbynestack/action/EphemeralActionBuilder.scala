package org.gatling.plugin.carbynestack.action

import io.carbynestack.ephemeral.client.{ActivationError, ActivationResult, EphemeralMultiClient}
import io.gatling.core.action.Action
import io.gatling.core.action.builder.ActionBuilder
import io.gatling.core.session.Session
import io.gatling.core.structure.ScenarioContext
import org.gatling.plugin.carbynestack.protocol.CsProtocol
import org.gatling.plugin.carbynestack.request.client.EphemeralClientBuilder

class EphemeralActionBuilder(
  clientBuilder: EphemeralClientBuilder,
  requestFunction: (EphemeralMultiClient, Session) => io.vavr.concurrent.Future[
    io.vavr.control.Either[ActivationError, java.util.List[ActivationResult]]
  ]
) extends ActionBuilder {
  override def build(ctx: ScenarioContext, next: Action): Action = {

    val csComponents = ctx.protocolComponentsRegistry.components(CsProtocol.CsProtocolKey)
    val coreComponents = ctx.coreComponents

    new EphemeralAction(clientBuilder.build(csComponents), requestFunction, coreComponents, next)
  }
}
