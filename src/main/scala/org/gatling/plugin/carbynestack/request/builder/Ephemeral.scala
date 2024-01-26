package org.gatling.plugin.carbynestack.request.builder

import io.gatling.commons.validation.{Failure, Success}
import io.gatling.core.session.Expression
import org.gatling.plugin.carbynestack.action.EphemeralActionBuilder
import org.gatling.plugin.carbynestack.request.client.EphemeralClientBuilder

import java.util.UUID

class Ephemeral {

  def execute(code: String, inputSecretIds: Expression[java.util.List[UUID]]): EphemeralActionBuilder =
    new EphemeralActionBuilder(
      new EphemeralClientBuilder(),
      (client, session) => {
        val inputSecretIdsValue = inputSecretIds(session) match {
          case Success(value)   => value
          case Failure(message) => throw new IllegalArgumentException(message)
        }
        client.execute(code, inputSecretIdsValue)
      }
    )
}
