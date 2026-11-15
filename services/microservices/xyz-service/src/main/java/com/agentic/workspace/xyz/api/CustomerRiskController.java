package com.agentic.workspace.xyz.api;

import com.agentic.workspace.xyz.dto.CustomerRiskResponse;
import com.agentic.workspace.xyz.service.CustomerRiskService;
import jakarta.validation.constraints.NotBlank;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Validated
@RestController
public class CustomerRiskController {

  private final CustomerRiskService customerRiskService;

  public CustomerRiskController(CustomerRiskService customerRiskService) {
    this.customerRiskService = customerRiskService;
  }

  @GetMapping("/xyz")
  public CustomerRiskResponse getCustomerRisk(
      @RequestParam("customerId") @NotBlank String customerId) {
    return customerRiskService.evaluate(customerId);
  }
}
