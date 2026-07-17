package com.agentic.workspace.qa.client;

import com.agentic.workspace.qa.config.ApiTestConfig;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.http.ContentType;
import io.restassured.specification.RequestSpecification;

public final class RestClientFactory {

  private RestClientFactory() {
  }

  public static RequestSpecification requestSpec(ApiTestConfig config) {
    return new RequestSpecBuilder()
        .setBaseUri(config.baseUri())
        .setPort(config.port())
        .setBasePath(config.basePath())
        .setAccept(ContentType.JSON)
        .log(LogDetail.URI)
        .build();
  }
}
