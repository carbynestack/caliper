/*
 * Copyright (c) 2023 - for information on the respective copyright owner
 * see the NOTICE file and/or the repository https://github.com/carbynestack/caliper.
 *
 * SPDX-License-Identifier: Apache-2.0
 */
package org.gatling.plugin.carbynestack.util

import io.carbynestack.amphora.common.{Tag, TagValueType}
import scala.jdk.CollectionConverters._

class TagGenerator(val tagKey: String, val tagValue: Long, val numberOfTags: Int) {

  def generate: java.util.List[Tag] = {
    (1 to numberOfTags).map { _ =>
      Tag
        .builder()
        .key(tagKey)
        .value(tagValue.toString)
        .valueType(TagValueType.LONG)
        .build()
    }.asJava
  }
}
