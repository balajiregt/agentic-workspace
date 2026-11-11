package com.agentic.workspace.qa.xyz.tests;

import static com.agentic.workspace.qa.assertions.JsonFieldAssertions.hasField;
import static com.agentic.workspace.qa.assertions.JsonFieldAssertions.hasRequiredField;
import static com.agentic.workspace.qa.fixtures.CustomerFixtures.HIGH_RISK_CUSTOMER;
import static com.agentic.workspace.qa.fixtures.CustomerFixtures.LOW_RISK_CUSTOMER;
import static com.agentic.workspace.qa.fixtures.CustomerFixtures.MEDIUM_RISK_CUSTOMER;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.emptyOrNullString;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.not;

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
    response.body("riskCategory", not(emptyOrNullString()));
    hasRequiredField(response, "decisionReason");
  }

  @Test
  @DisplayName("GET /xyz returns medium risk response for review customer")
  void getCustomerRiskReturnsMediumRiskCustomer() {
    var response = given(requestSpec)
        .queryParam("customerId", MEDIUM_RISK_CUSTOMER)
        .when()
        .get("/xyz")
        .then()
        .statusCode(200)
        .body("customerId", equalTo(MEDIUM_RISK_CUSTOMER))
        .body("eligible", equalTo(true))
        .body("riskCategory", equalTo("MEDIUM"))
        .body("score", equalTo(57))
        .body("decisionReason", equalTo("Customer is eligible with standard monitoring."));

    response.body("riskCategory", not(emptyOrNullString()));
    hasRequiredField(response, "decisionReason");
  }

  @Test
  @DisplayName("GET /xyz returns high risk response for blocked customer")
  void getCustomerRiskReturnsHighRiskCustomer() {
    var response = given(requestSpec)
        .queryParam("customerId", HIGH_RISK_CUSTOMER)
        .when()
        .get("/xyz")
        .then()
        .statusCode(200)
        .body("customerId", equalTo(HIGH_RISK_CUSTOMER))
        .body("eligible", equalTo(false))
        .body("riskCategory", equalTo("HIGH"));

    response.body("riskCategory", not(emptyOrNullString()));
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

  @Test
  @DisplayName("GET /xyz rejects blank customerId")
  void getCustomerRiskRejectsBlankCustomerId() {
    given(requestSpec)
        .queryParam("customerId", " ")
        .when()
        .get("/xyz")
        .then()
        .statusCode(400)
        .body("error", equalTo("Bad Request"))
        .body("message", containsString("customerId"));
  }
}
