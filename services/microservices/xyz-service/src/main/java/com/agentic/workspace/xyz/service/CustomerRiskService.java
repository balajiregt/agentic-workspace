package com.agentic.workspace.xyz.service;

import com.agentic.workspace.xyz.domain.RiskCategory;
import com.agentic.workspace.xyz.dto.CustomerRiskResponse;
import org.springframework.stereotype.Service;

@Service
public class CustomerRiskService {

  public CustomerRiskResponse evaluate(String customerId) {
    String normalizedCustomerId = customerId.trim().toUpperCase();
    int score = calculateScore(normalizedCustomerId);
    RiskCategory riskCategory = riskCategoryFor(score);
    boolean eligible = riskCategory != RiskCategory.HIGH;

    return new CustomerRiskResponse(
        normalizedCustomerId,
        eligible,
        riskCategory,
        score,
        decisionReasonFor(riskCategory));
  }

  private int calculateScore(String customerId) {
    if (customerId.endsWith("9999") || customerId.contains("BLOCK")) {
      return 91;
    }

    if (customerId.endsWith("5000") || customerId.contains("REVIEW")) {
      return 57;
    }

    return 18;
  }

  private RiskCategory riskCategoryFor(int score) {
    if (score >= 80) {
      return RiskCategory.HIGH;
    }

    if (score >= 40) {
      return RiskCategory.MEDIUM;
    }

    return RiskCategory.LOW;
  }

  private String decisionReasonFor(RiskCategory riskCategory) {
    return switch (riskCategory) {
      case HIGH -> "Customer requires manual review before eligibility.";
      case MEDIUM -> "Customer is eligible with standard monitoring.";
      case LOW -> "Customer is eligible with low risk signals.";
    };
  }
}
