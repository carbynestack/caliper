/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
import io.carbynestack.amphora.common.{TagFilter, TagFilterOperator}
import io.gatling.app.Gatling
import io.gatling.core.Predef._
import io.gatling.core.config.GatlingPropertiesBuilder
import org.gatling.plugin.carbynestack.PreDef._
import org.gatling.plugin.carbynestack.util.{SecretGenerator, TagGenerator}

import scala.jdk.CollectionConverters._
import scala.util.Random

class CarbynestackSimulation extends Simulation {

  val csProtocol = cs
    .endpoints(List("http://172.18.1.128/amphora", "http://172.18.2.128/amphora"))
    .prime("198766463529478683931867765928436695041")
    .r("141515903391459779531506841503331516415")
    .invR("133854242216446749056083838363708373830")

  val tagKeys = List.fill[String](2)(Random.alphanumeric.take(10).mkString)
  val tagGenerator = new TagGenerator(tagKeys, Some(1000000000L), Some(9999999999L), null)
  val secretGenerator = new SecretGenerator(tagGenerator, 1000000000L, 9999999999L, 1)

  val feeder = Iterator.continually {
    Map("secret" -> secretGenerator.generate)
  }

  val createSecret = scenario("Amphora-createSecret-scenario")
    .feed(feeder)
    .exec(amphora.createSecret("#{secret}"))

  val getSecrets = scenario("Amphora-getSecrets-scenario")
    .exec(amphora.getSecrets())

  setUp(getSecrets.inject(atOnceUsers(10)).protocols(csProtocol))
}

object Main {
  def main(args: Array[String]): Unit =
    Gatling.fromMap(
      (new GatlingPropertiesBuilder)
        .simulationClass(classOf[CarbynestackSimulation].getName)
        .build,
    )
}
