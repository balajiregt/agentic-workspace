package com.agentic.workspace.xyz.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.agentic.workspace.xyz.domain.RiskCategory;
import com.agentic.workspace.xyz.dto.CustomerRiskResponse;
import org.junit.jupiter.api.Test;

class CustomerRiskServiceTest {

  private final CustomerRiskService service = new CustomerRiskService();

  @Test
  void evaluatesLowRiskCustomerAsEligible() {
    CustomerRiskResponse response = service.evaluate("cust-1001");

    assertThat(response.customerId()).isEqualTo("CUST-1001");
    assertThat(response.eligible()).isTrue();
    assertThat(response.riskCategory()).isEqualTo(RiskCategory.LOW);
  }

  @Test
  void evaluatesBlockedCustomerAsHighRisk() {
    CustomerRiskResponse response = service.evaluate("cust-9999");

    assertThat(response.eligible()).isFalse();
    assertThat(response.riskCategory()).isEqualTo(RiskCategory.HIGH);
  }
}
