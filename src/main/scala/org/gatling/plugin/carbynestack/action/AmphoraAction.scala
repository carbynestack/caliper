package org.gatling.plugin.carbynestack.action

import io.carbynestack.amphora.client.{AmphoraClient, Secret}
import io.carbynestack.amphora.common.Metadata
import io.gatling.commons.stats.{KO, OK}
import io.gatling.core.CoreComponents
import io.gatling.core.action.Action
import io.gatling.core.session.Session
import io.gatling.core.util.NameGen

import scala.jdk.CollectionConverters._
import scala.util.control.NonFatal

class AmphoraAction[R](
  client: AmphoraClient,
  requestFunction: (AmphoraClient, Session) => R,
  coreComponents: CoreComponents,
  val next: Action
) extends Action
    with NameGen {

  override def name: String = genName("AmphoraAction")

  override def execute(session: Session): Unit = {

    val start = coreComponents.clock.nowMillis
    var stop = start
    val uuids: java.util.List[java.util.UUID] = new java.util.ArrayList[java.util.UUID]()
    try {

      val response: R = requestFunction(client, session)
      stop = coreComponents.clock.nowMillis

      response match {
        case uuid: java.util.UUID => uuids.add(uuid)
        case list: java.util.List[_] =>
          list.asScala.foreach {
            case metadata: Metadata => uuids.add(metadata.getSecretId)
          }
        case _: Secret =>
        case _: Unit =>
        case other => throw new IllegalArgumentException(s"Unexpected response type: ${other.getClass.getName}")
      }
      val modifiedSession = if (!uuids.isEmpty) session.set("uuids", uuids) else session

      coreComponents.statsEngine.logResponse(
        modifiedSession.scenario,
        modifiedSession.groups,
        name,
        start,
        stop,
        OK,
        None,
        None
      )
      next ! modifiedSession
    } catch {
      case NonFatal(e) =>
        logger.error(e.getMessage, e)
        coreComponents.statsEngine.logResponse(
          session.scenario,
          session.groups,
          name,
          start,
          stop,
          KO,
          Some("500"),
          Some(e.getMessage),
        )
        next ! session.markAsFailed
    }
  }
}
