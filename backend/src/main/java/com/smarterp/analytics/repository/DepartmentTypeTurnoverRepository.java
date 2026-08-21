package com.smarterp.analytics.repository;

import com.smarterp.analytics.domain.DepartmentTypeTurnover;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DepartmentTypeTurnoverRepository extends JpaRepository<DepartmentTypeTurnover, String> {
    
    // You get findAll() out of the box to fetch the stats for all department types!
    
}