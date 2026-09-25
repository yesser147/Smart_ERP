package com.smarterp.hr.service;

import com.smarterp.hr.domain.Employee;
import com.smarterp.hr.domain.LeaveRequest;
import com.smarterp.hr.dto.LeaveRequestCreateDTO;
import com.smarterp.hr.repository.EmployeeRepository;
import com.smarterp.hr.repository.LeaveRequestRepository;
import com.smarterp.shared.audit.AuditService;
import com.smarterp.shared.exception.BadRequestException;
import com.smarterp.shared.notification.NotificationService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDate;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class LeaveServiceTest {

    @Mock LeaveRequestRepository repository;
    @Mock EmployeeRepository employeeRepository;
    @Mock NotificationService notificationService;
    @Mock AuditService auditService;
    @InjectMocks LeaveService service;

    @Test
    void endDateBeforeStartDateIsRefused() {
        var req = new LeaveRequestCreateDTO("ANNUAL", LocalDate.of(2026, 5, 10), LocalDate.of(2026, 5, 1), null);
        assertThatThrownBy(() -> service.request(1L, req)).isInstanceOf(BadRequestException.class);
        verifyNoInteractions(repository);
    }

    @Test
    void decisionNotifiesTheEmployeeAndCannotBeRepeated() {
        Employee e = new Employee();
        e.setEmployeeId(7L);
        e.setFirstName("Sam");
        e.setLastName("Lee");
        LeaveRequest leave = new LeaveRequest();
        leave.setEmployee(e);
        leave.setLeaveType("ANNUAL");
        leave.setStartDate(LocalDate.of(2026, 6, 1));
        leave.setEndDate(LocalDate.of(2026, 6, 5));
        when(repository.findById(3L)).thenReturn(Optional.of(leave));

        var dto = service.decide(3L, true);

        assertThat(dto.status()).isEqualTo("APPROVED");
        assertThat(dto.days()).isEqualTo(5);
        verify(notificationService).notifyEmployee(eq(7L), anyString(), anyString(), anyString());
        assertThatThrownBy(() -> service.decide(3L, false)).isInstanceOf(BadRequestException.class);
    }

    @Test
    void formerEmployeesAndPastDatesAreRefused() {
        LocalDate next = LocalDate.now().plusDays(10);
        Employee left = new Employee();
        left.setEmployeeStatus("Voluntarily Terminated");
        when(employeeRepository.findById(9L)).thenReturn(Optional.of(left));
        assertThatThrownBy(() -> service.request(9L, new LeaveRequestCreateDTO("ANNUAL", next, next.plusDays(2), null)))
                .isInstanceOf(BadRequestException.class);

        LocalDate past = LocalDate.now().minusDays(3);
        assertThatThrownBy(() -> service.request(9L, new LeaveRequestCreateDTO("ANNUAL", past, past.plusDays(1), null)))
                .isInstanceOf(BadRequestException.class);
        verifyNoInteractions(repository);
    }
}
