/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.protocol

import io.gatling.core.protocol.ProtocolComponents
import io.gatling.core.session.Session

case class CsComponents(protocol: CsProtocol) extends ProtocolComponents {

  override def onStart: Session => Session = Session.Identity

  override def onExit: Session => Unit = ProtocolComponents.NoopOnExit
}
