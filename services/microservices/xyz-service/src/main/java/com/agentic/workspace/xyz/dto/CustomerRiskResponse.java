package com.agentic.workspace.xyz.dto;

import com.agentic.workspace.xyz.domain.RiskCategory;

public record CustomerRiskResponse(
    String customerId,
    boolean eligible,
    RiskCategory riskCategory,
    int score,
    String decisionReason) {
}
