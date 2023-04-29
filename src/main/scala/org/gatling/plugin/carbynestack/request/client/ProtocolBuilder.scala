/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.request.client

import org.gatling.plugin.carbynestack.protocol.CsComponents

trait ProtocolBuilder[C] {

  def build(csComponents: CsComponents): C
}
