package com.smarterp.hr.repository;

import com.smarterp.hr.domain.Employee;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.List;

public interface EmployeeRepository extends JpaRepository<Employee, Long> {

    long countByIsDeletedFalse();

    long countByIsDeletedFalseAndEmployeeStatusIn(Collection<String> statuses);

    /** Name or title search, for the paged employee list. */
    @Query(value = """
        SELECT e FROM Employee e
        JOIN FETCH e.department
        WHERE (:search IS NULL OR :search = ''
               OR LOWER(CONCAT(e.firstName, ' ', e.lastName)) LIKE LOWER(CONCAT('%', :search, '%'))
               OR LOWER(e.title) LIKE LOWER(CONCAT('%', :search, '%')))
    """, countQuery = """
        SELECT COUNT(e) FROM Employee e
        WHERE (:search IS NULL OR :search = ''
               OR LOWER(CONCAT(e.firstName, ' ', e.lastName)) LIKE LOWER(CONCAT('%', :search, '%'))
               OR LOWER(e.title) LIKE LOWER(CONCAT('%', :search, '%')))
    """)
    Page<Employee> findPageWithSearch(@Param("search") String search, Pageable pageable);

    /** Active employees with their team, for the payroll export. */
    @Query("""
        SELECT e FROM Employee e
        LEFT JOIN FETCH e.department
        WHERE e.isDeleted = false AND UPPER(e.employeeStatus) IN ('ACTIVE', 'ON LEAVE')
        ORDER BY e.lastName, e.firstName
    """)
    List<Employee> findActiveWithDepartment();
}
