package com.agentic.workspace.xyz.exception;

import jakarta.validation.ConstraintViolationException;
import java.time.OffsetDateTime;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

  @ExceptionHandler({
      ConstraintViolationException.class,
      MissingServletRequestParameterException.class
  })
  public ResponseEntity<Map<String, Object>> handleBadRequest(Exception exception) {
    return ResponseEntity.badRequest().body(Map.of(
        "timestamp", OffsetDateTime.now().toString(),
        "status", HttpStatus.BAD_REQUEST.value(),
        "error", "Bad Request",
        "message", exception.getMessage()));
  }
}
