package simulation

import io.carbynestack.amphora.client.Secret
import io.carbynestack.amphora.common.{Tag, TagValueType}
import io.gatling.app.Gatling
import io.gatling.core.Predef._
import io.gatling.core.config.GatlingPropertiesBuilder
import org.gatling.plugin.carbynestack.PreDef._

import scala.jdk.CollectionConverters._
import scala.util.Random

class AmphoraSimulation extends Simulation {

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

  val csProtocol = cs
    .endpoints(List(apolloFqdn, starbuckFqdn).map(fqdn => "http://" + fqdn))
    .prime(prime)
    .r(r)
    .invR(invR)

  val numberOfTags = 100
  val lengthOfTag = 100
  val secretValueLowerBound = 1000000000L
  val secretValueUpperBound = 9999999999L

  val tags: java.util.List[Tag] =
    List
      .fill[(String, String)](numberOfTags)(
        Random.alphanumeric.take(lengthOfTag).mkString,
        Random.alphanumeric.take(lengthOfTag).mkString
      )
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

  val generateSecret: Int => Secret = (numberOfSecretValuesPerSecret: Int) => {

    val secretValues = Array.fill[java.math.BigInteger](numberOfSecretValuesPerSecret)(
      new java.math.BigInteger(
        (secretValueLowerBound + Random.nextLong(secretValueUpperBound - secretValueLowerBound)).toString
      )
    )
    Secret.of(tags, secretValues)
  }

  val generateFeeder: Int => Iterator[Map[String, Secret]] = (numberOfSecretValues: Int) => {
    Iterator.continually {
      Map("secret" -> generateSecret(numberOfSecretValues))
    }
  }

  def performCreateSecretRequest(feeder: Iterator[Map[String, Secret]], repeats: Int, groupLabel: String) = {
    group(groupLabel) {
      repeat(repeats) {
        feed(feeder)
          .exec(amphora.createSecret(("#{secret}")))
          .pause(5)
      }
    }
  }

  def performGetSecretRequest(groupLabel: String) = {
    exec(amphora.getSecrets())
      .group(groupLabel) {
        repeat(1) {
          foreach("#{uuids}", "uuid") {
            exec(amphora.getSecret("#{uuid}"))
              .pause(5)
          }
        }
      }
  }

  def deleteAllSecretes() = {
    exec(amphora.getSecrets())
      .exec(group("deleteSecret_all ") {
        foreach("#{uuids}", "uuid") {
          exec(amphora.deleteSecret("#{uuid}"))
            .pause(5)
        }
      })
  }

  val singleUserScenario = scenario("single_user_scenario")
    .exec(performCreateSecretRequest(generateFeeder(1000), 1, "createSecret_1000")) //1000
    .pause(60 * 3)
    .exec(performGetSecretRequest("getSecret_1000")) //3000
    .pause(60 * 3)
    .exec(performCreateSecretRequest(generateFeeder(10000), 1, "createSecret_10000")) //13000
    .pause(60 * 3)
    .exec(performGetSecretRequest("getSecret_11000")) //35000
    .pause(60 * 3)
    .exec(performCreateSecretRequest(generateFeeder(50000), 1, "createSecret_50000")) //85000
    .pause(60 * 3)
    .exec(performGetSecretRequest("getSecret_61000")) //207000
    .pause(60 * 3)
    .exec(performCreateSecretRequest(generateFeeder(100000), 1, "createSecret_100000")) //307000
    .pause(60 * 3)
    .exec(performGetSecretRequest("getSecret_161000")) //629000
    .pause(60 * 3)
    .exec(performCreateSecretRequest(generateFeeder(100000), 1, "")) //729000
    .pause(60 * 10) // genereate tuples
    .exec(performGetSecretRequest("getSecret_261000")) //522000
    .pause(60 * 3)
    .exec(performCreateSecretRequest(generateFeeder(250000), 1, "createSecret_250000")) //772000
    .pause(60 * 10) // genereate tuples
    .exec(performCreateSecretRequest(generateFeeder(400000), 1, "createSecret_400000")) //400000
    .pause(60 * 10) // genereate tuples
    .exec(deleteAllSecretes())
    .pause(60 * 3)

  val responseTimesScenario = scenario("response_times_scenario")
    .exec(performCreateSecretRequest(generateFeeder(1000), 10, "createSecret_1000_repeat_10")) //10000
    .pause(60 * 3)
    .exec(performGetSecretRequest("getSecret_1000_repeat_10")) //30000
    .pause(60 * 3)
    .exec(performCreateSecretRequest(generateFeeder(10000), 10, "createSecret_10000_repeat_10")) //130000
    .pause(60 * 3)
    .exec(performGetSecretRequest("getSecret_10000_repeat_10")) //330000
    .pause(60 * 3)
    .exec(performCreateSecretRequest(generateFeeder(50000), 10, "createSecret_50000_repeat_10")) //830000
    .pause(60 * 10) // genereate tuples
    .exec(performCreateSecretRequest(generateFeeder(100000), 5, "createSecret_100000_repeat_5")) //500000
    .pause(60 * 3)
    .exec(deleteAllSecretes())
    .pause(60 * 3)

  val delete = scenario("delete")
    .exec(deleteAllSecretes())

  setUp(
    singleUserScenario
      .inject(atOnceUsers(1))
      .andThen(responseTimesScenario.inject(atOnceUsers(1)))
  ).protocols(csProtocol)
}

object Main {
  def main(args: Array[String]): Unit =
    Gatling.fromMap(
      (new GatlingPropertiesBuilder)
        .simulationClass(classOf[AmphoraSimulation].getName)
        .build,
    )
}
