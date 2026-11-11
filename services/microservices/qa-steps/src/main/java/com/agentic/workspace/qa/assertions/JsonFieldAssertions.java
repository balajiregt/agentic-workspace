package com.agentic.workspace.qa.assertions;

import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.notNullValue;

import io.restassured.response.ValidatableResponse;

public final class JsonFieldAssertions {

  private JsonFieldAssertions() {
  }

  public static ValidatableResponse hasField(
      ValidatableResponse response,
      String jsonPath,
      Object expectedValue) {
    return response.body(jsonPath, equalTo(expectedValue));
  }

  public static ValidatableResponse hasRequiredField(
      ValidatableResponse response,
      String jsonPath) {
    return response.body(jsonPath, notNullValue());
  }
}
