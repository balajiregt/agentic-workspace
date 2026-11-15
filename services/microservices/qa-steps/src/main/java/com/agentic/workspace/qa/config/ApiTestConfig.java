package com.agentic.workspace.qa.config;

public record ApiTestConfig(String baseUri, int port, String basePath) {

  public static ApiTestConfig fromSystemProperties() {
    return new ApiTestConfig(
        System.getProperty("api.baseUri", "http://localhost"),
        Integer.getInteger("api.port", 8080),
        System.getProperty("api.basePath", ""));
  }
}
