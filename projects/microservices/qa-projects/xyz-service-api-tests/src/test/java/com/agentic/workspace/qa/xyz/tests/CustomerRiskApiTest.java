package com.agentic.workspace.qa.xyz.tests;

import static com.agentic.workspace.qa.assertions.JsonFieldAssertions.hasField;
import static com.agentic.workspace.qa.assertions.JsonFieldAssertions.hasRequiredField;
import static com.agentic.workspace.qa.fixtures.CustomerFixtures.HIGH_RISK_CUSTOMER;
import static com.agentic.workspace.qa.fixtures.CustomerFixtures.LOW_RISK_CUSTOMER;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;

import com.agentic.workspace.qa.client.RestClientFactory;
import com.agentic.workspace.qa.config.ApiTestConfig;
import io.restassured.specification.RequestSpecification;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class CustomerRiskApiTest {

  private static RequestSpecification requestSpec;

  @BeforeAll
  static void configureClient() {
    requestSpec = RestClientFactory.requestSpec(ApiTestConfig.fromSystemProperties());
  }

  @Test
  @DisplayName("GET /xyz returns low risk response for eligible customer")
  void getCustomerRiskReturnsLowRiskCustomer() {
    var response = given(requestSpec)
        .queryParam("customerId", LOW_RISK_CUSTOMER)
        .when()
        .get("/xyz")
        .then()
        .statusCode(200);

    hasField(response, "customerId", LOW_RISK_CUSTOMER);
    hasField(response, "eligible", true);
    hasField(response, "riskCategory", "LOW");
    hasRequiredField(response, "decisionReason");
  }

  @Test
  @DisplayName("GET /xyz returns high risk response for blocked customer")
  void getCustomerRiskReturnsHighRiskCustomer() {
    given(requestSpec)
        .queryParam("customerId", HIGH_RISK_CUSTOMER)
        .when()
        .get("/xyz")
        .then()
        .statusCode(200)
        .body("customerId", equalTo(HIGH_RISK_CUSTOMER))
        .body("eligible", equalTo(false))
        .body("riskCategory", equalTo("HIGH"));
  }

  @Test
  @DisplayName("GET /xyz rejects missing customerId")
  void getCustomerRiskRejectsMissingCustomerId() {
    given(requestSpec)
        .when()
        .get("/xyz")
        .then()
        .statusCode(400)
        .body("error", equalTo("Bad Request"));
  }
}
