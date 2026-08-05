package com.smarterp.hr.dto;

import java.util.UUID;

public record DepartmentDTO(
    UUID id,
    String name,
    String description,
    UUID managerId,
    String managerName
) {}