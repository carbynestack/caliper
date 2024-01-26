package org.gatling.plugin.carbynestack.request.client
import io.carbynestack.ephemeral.client.{EphemeralEndpoint, EphemeralMultiClient}
import org.gatling.plugin.carbynestack.protocol.CsComponents

import java.net.URI
import scala.jdk.CollectionConverters._

class EphemeralClientBuilder extends ClientBuilder[EphemeralMultiClient] {

  override def build(csComponents: CsComponents): EphemeralMultiClient = {

    new EphemeralMultiClient.Builder()
      .withEndpoints(
        csComponents.protocol.ephemeralEndpoints
          .map(
            uri =>
              EphemeralEndpoint
                .Builder()
                .withServiceUri(URI.create(uri))
                .withApplication(csComponents.protocol.program)
                .build()
          )
          .asJava
      )
      .build()
  }
}
