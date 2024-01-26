/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.request.builder

import io.carbynestack.amphora.client.Secret
import io.carbynestack.amphora.common.Metadata
import io.gatling.commons.validation.{Failure, Success}
import io.gatling.core.session.Expression
import org.gatling.plugin.carbynestack.action.AmphoraActionBuilder
import org.gatling.plugin.carbynestack.request.client.AmphoraClientBuilder

class Amphora() {

  def createSecret(secret: Expression[Secret]): AmphoraActionBuilder[java.util.UUID] =
    new AmphoraActionBuilder[java.util.UUID](
      new AmphoraClientBuilder,
      (client, session) => {
        val secretValue = secret(session) match {
          case Success(value) => value
          case Failure(message) => throw new IllegalArgumentException(message)
        }
        client.createSecret(secretValue)
      }
    )

  def getSecrets(): AmphoraActionBuilder[java.util.List[Metadata]] =
    new AmphoraActionBuilder[java.util.List[Metadata]](
      new AmphoraClientBuilder,
      (client, _) => client.getSecrets()
    )

  def getSecret(uuid: Expression[java.util.UUID]): AmphoraActionBuilder[Secret] =
    new AmphoraActionBuilder[Secret](
      new AmphoraClientBuilder,
      (client, session) => {
        val uuidValue = uuid(session) match{
          case Success(value) => value
          case Failure(message) => throw new IllegalArgumentException(message)
        }
        client.getSecret(uuidValue)
      }
    )

  def deleteSecret(uuid: Expression[java.util.UUID]): AmphoraActionBuilder[Unit] =
    new AmphoraActionBuilder[Unit](
      new AmphoraClientBuilder,
      (client, session) => {
        val uuidValue = uuid(session) match {
          case Success(value) => value
          case Failure(message) => throw new IllegalArgumentException(message)
        }
        client.deleteSecret(uuidValue)
      }
    )
}
