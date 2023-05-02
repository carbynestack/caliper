/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.util

import io.carbynestack.amphora.common.{Tag, TagValueType}

import scala.jdk.CollectionConverters._
import scala.util.Random

class TagGenerator(
  val tagKeys: List[String],
  val lowerBound: Option[Long],
  val upperBound: Option[Long],
  val stringLength: Option[Int]
) {

  def generate: java.util.List[Tag] = {
    tagKeys.map { tagKey =>
      Tag
        .builder()
        .key(tagKey)
        .value(
          if (lowerBound.isDefined && upperBound.isDefined)
            (lowerBound.get + Random.nextLong(upperBound.get - lowerBound.get)).toString
          else Random.alphanumeric.take(stringLength.get).mkString
        )
        .valueType(if (lowerBound.isDefined && upperBound.isDefined) TagValueType.LONG else TagValueType.STRING)
        .build()
    }.asJava
  }
}
