/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.request.builder

import io.carbynestack.amphora.client.{AmphoraClient, Secret}
import io.carbynestack.amphora.common.paging.Sort
import io.carbynestack.amphora.common.{Metadata, TagFilter}
import io.gatling.commons.validation.{Failure, Success}
import io.gatling.core.session.{Expression, Session}
import org.gatling.plugin.carbynestack.action.CsActionBuilder
import org.gatling.plugin.carbynestack.request.client.AmphoraProtocolBuilder

class Amphora() {

  def createSecret(secret: Expression[Secret]): CsActionBuilder[AmphoraClient, java.util.UUID] =
    new CsActionBuilder[AmphoraClient, java.util.UUID](
      new AmphoraProtocolBuilder(),
      (client: AmphoraClient, session: Session) => {
        val secretValue = secret(session) match {
          case Success(value)   => value
          case Failure(message) => throw new IllegalArgumentException(message)
        }
        client.createSecret(secretValue)
      }
    )

  def getSecrets(): CsActionBuilder[AmphoraClient, java.util.List[Metadata]] =
    new CsActionBuilder[AmphoraClient, java.util.List[Metadata]](
      new AmphoraProtocolBuilder(),
      (client: AmphoraClient, _: Session) => {
        client.getSecrets
      }
    )

  def getSecrets(filterCriteria: java.util.List[TagFilter]): CsActionBuilder[AmphoraClient, java.util.List[Metadata]] =
    new CsActionBuilder[AmphoraClient, java.util.List[Metadata]](
      new AmphoraProtocolBuilder(),
      (client: AmphoraClient, _: Session) => { client.getSecrets(filterCriteria) }
    )

  def getSecrets(sort: Sort): CsActionBuilder[AmphoraClient, java.util.List[Metadata]] =
    new CsActionBuilder[AmphoraClient, java.util.List[Metadata]](
      new AmphoraProtocolBuilder(),
      (client: AmphoraClient, _: Session) => {
        client.getSecrets(sort)
      }
    )
}
