package org.gatling.plugin.carbynestack.action

import io.carbynestack.ephemeral.client.{ActivationError, ActivationResult, EphemeralMultiClient}
import io.gatling.commons.stats.{KO, OK}
import io.gatling.core.CoreComponents
import io.gatling.core.action.Action
import io.gatling.core.session.Session
import io.gatling.core.util.NameGen
import io.vavr.concurrent.Future

import scala.util.control.NonFatal

class EphemeralAction(
  client: EphemeralMultiClient,
  requestFunction: (EphemeralMultiClient, Session) => Future[
    io.vavr.control.Either[ActivationError, java.util.List[ActivationResult]]
  ],
  coreComponents: CoreComponents,
  val next: Action
) extends Action
    with NameGen {

  override def name: String = genName("EphemeralAction")

  override def execute(session: Session): Unit = {

    val start = coreComponents.clock.nowMillis
    try {

      val response: Future[io.vavr.control.Either[ActivationError, java.util.List[ActivationResult]]] =
        requestFunction(client, session)

      response.await()
      response.get().get()

      coreComponents.statsEngine.logResponse(
        session.scenario,
        session.groups,
        name,
        start,
        coreComponents.clock.nowMillis,
        OK,
        None,
        None
      )
      next ! session
    } catch {
      case NonFatal(e) =>
        logger.error(e.getMessage, e)
        coreComponents.statsEngine.logResponse(
          session.scenario,
          session.groups,
          name,
          start,
          coreComponents.clock.nowMillis,
          KO,
          Some("500"),
          Some(e.getMessage),
        )
        next ! session.markAsFailed
    }
  }
}
