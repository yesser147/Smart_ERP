package com.smarterp.hr.repository;

import com.smarterp.hr.domain.Employee;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
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

    /** Current employees who have no login yet (admin "New account"). */
    @Query("""
        SELECT e FROM Employee e
        LEFT JOIN FETCH e.department
        WHERE e.isDeleted = false AND UPPER(e.employeeStatus) IN ('ACTIVE', 'ON LEAVE')
          AND NOT EXISTS (SELECT u FROM User u WHERE u.employeeId = e.employeeId)
          AND (:search IS NULL OR :search = ''
               OR LOWER(CONCAT(e.firstName, ' ', e.lastName)) LIKE LOWER(CONCAT('%', :search, '%'))
               OR LOWER(e.title) LIKE LOWER(CONCAT('%', :search, '%')))
        ORDER BY e.lastName, e.firstName
    """)
    List<Employee> findWithoutAccount(@Param("search") String search, Pageable pageable);

    /** Active employees with an approved leave covering `day` become "On Leave". */
    @Modifying
    @Query("""
        UPDATE Employee e SET e.employeeStatus = 'On Leave'
        WHERE UPPER(e.employeeStatus) = 'ACTIVE' AND e.employeeId IN (
            SELECT l.employee.employeeId FROM LeaveRequest l
            WHERE l.status = 'APPROVED' AND l.startDate <= :day AND l.endDate >= :day)
    """)
    int startApprovedLeaves(@Param("day") LocalDate day);

    /** Employees back from an approved leave (and not on another one) become "Active" again.
     *  Only people put on leave by a leave request are touched. */
    @Modifying
    @Query("""
        UPDATE Employee e SET e.employeeStatus = 'Active'
        WHERE UPPER(e.employeeStatus) = 'ON LEAVE'
          AND e.employeeId IN (
            SELECT l.employee.employeeId FROM LeaveRequest l
            WHERE l.status = 'APPROVED' AND l.endDate < :day)
          AND e.employeeId NOT IN (
            SELECT l2.employee.employeeId FROM LeaveRequest l2
            WHERE l2.status = 'APPROVED' AND l2.startDate <= :day AND l2.endDate >= :day)
    """)
    int endFinishedLeaves(@Param("day") LocalDate day);
}
