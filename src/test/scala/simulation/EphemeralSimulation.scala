package simulation

import io.carbynestack.amphora.client.Secret
import io.carbynestack.amphora.common.{Tag, TagValueType}
import io.gatling.core.Predef._
import org.gatling.plugin.carbynestack.PreDef._

import scala.jdk.CollectionConverters._

class EphemeralSimulation extends Simulation {

  val apolloFqdn: String = sys.env.get("APOLLO_FQDN") match {
    case Some(fqdn) => fqdn
    case None => throw new IllegalStateException("Environment variable APOLLO_FQDN not set")
  }

  val starbuckFqdn: String = sys.env.get("STARBUCK_FQDN") match {
    case Some(fqdn) => fqdn
    case None => throw new IllegalStateException("Environment variable STARBUCK_FQDN not set")
  }

  val prime: String = sys.env.get("PRIME") match {
    case Some(prime) => prime
    case None => throw new IllegalStateException("Environment variable PRIME not set")
  }

  val r: String = sys.env.get("R") match {
    case Some(r) => r
    case None => throw new IllegalStateException("Environment variable R not set")
  }

  val invR: String = sys.env.get("INVR") match {
    case Some(invR) => invR
    case None => throw new IllegalStateException("Environment variable INVR not set")
  }

  val program: String = sys.env.get("PROGRAM") match {
    case Some(program) => program
    case None => throw new IllegalStateException("Environment variable PROGRAM not set")
  }

  val csProtocol = cs
    .endpoints(List(apolloFqdn, starbuckFqdn).map(fqdn => "http://" + fqdn))
    .prime(prime)
    .r(r)
    .invR(invR)
    .program(program)

  val vectorATag: java.util.List[Tag] =
    List(("vector", "a"))
      .map(
        x =>
          Tag
            .builder()
            .key(x._1)
            .value(x._2)
            .valueType(TagValueType.STRING)
            .build()
      )
      .asJava

  val vectorBTag: java.util.List[Tag] =
    List(("vector", "b"))
      .map(
        x =>
          Tag
            .builder()
            .key(x._1)
            .value(x._2)
            .valueType(TagValueType.STRING)
            .build()
      )
      .asJava

  val numberOfSecretValues: Int = 10
  val dataSize: Int = numberOfSecretValues * 2
  val secretValue: String = "10"

  val feeder = Iterator.continually {
    Map(
      "secret" -> Secret
        .of(vectorBTag, Array.fill[java.math.BigInteger](numberOfSecretValues)(new java.math.BigInteger(secretValue)))
    )
  }

  def performDeleteSecretRequest() = {
    exec(amphora.getSecrets())
      .foreach("#{uuids}", "uuid") {
        exec(amphora.deleteSecret("#{uuid}"))
      }
  }

  val scalarValueProgram: String =
    s"""port=regint(10000)
       |listen(port)
       |socket_id = regint()
       |acceptclientconnection(socket_id, port)
       |data = Array.create_from(sint.read_from_socket(socket_id, $dataSize))
       |scalar_product = Array(1, sint)
       |@for_range($numberOfSecretValues)
       |def f(i):
       |   scalar_product[0] += data[i] * data[$numberOfSecretValues + i]
       |sint.write_to_socket(socket_id, scalar_product)""".stripMargin

  val scalarValueProgramOpt: String =
    s"""port=regint(10000)
       |listen(port)
       |socket_id = regint()
       |acceptclientconnection(socket_id, port)
       |data = Array.create_from(sint.read_from_socket(socket_id, $dataSize))
       |scalar_product = Array(1, sint)
       |@for_range_opt($numberOfSecretValues)
       |def f(i):
       |   scalar_product[0] += data[i] * data[$numberOfSecretValues + i]
       |sint.write_to_socket(socket_id, scalar_product)""".stripMargin

  val emptyProgram: String =
    s"""port=regint(10000)
       |listen(port)
       |socket_id = regint()
       |acceptclientconnection(socket_id, port)
       |data = Array.create_from(sint.read_from_socket(socket_id, $dataSize))
       |result = Array($dataSize, sint)
       |@for_range($dataSize)
       |def f(i):
       |   result[i] = data[i]
       |sint.write_to_socket(socket_id, result)""".stripMargin

  val emptyProgramScenario = scenario("emptyProgramScenario")
    .feed(feeder)
    .exec(amphora.createSecret("#{secret}"))
    .feed((feeder))
    .exec(amphora.createSecret("#{secret}"))
    .exec(amphora.getSecrets())
    .group("execute_empty") {
      repeat(1) {
        exec(ephemeral.execute(emptyProgram, "#{uuids}"))
      }
    }
    .exec(performDeleteSecretRequest())
    .pause(60 * 3)

  val scalarValueOptProgramScenario = scenario("scalarValueOptProgramScenario")
    .feed(feeder)
    .exec(amphora.createSecret("#{secret}"))
    .feed((feeder))
    .exec(amphora.createSecret("#{secret}"))
    .exec(amphora.getSecrets())
    .group("execute_scalarValue") {
      repeat(1) {
        exec(ephemeral.execute(scalarValueProgramOpt, "#{uuids}"))
      }
    }
    .exec(performDeleteSecretRequest())
    .pause(60 * 3)

  setUp(
    emptyProgramScenario
      .inject(atOnceUsers(1))
      .andThen(scalarValueOptProgramScenario.inject(atOnceUsers(1)))
  ).protocols(csProtocol)
}
