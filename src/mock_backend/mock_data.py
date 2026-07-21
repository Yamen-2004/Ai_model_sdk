"""Static mock Case data, keyed by id.

Reuses `loan_restructuring_sdk.models.case_dto.Case` (and its nested
models) directly rather than defining a parallel schema here -- this mock
backend exists specifically to hand the SDK exactly the payload shape it
expects, so importing the same Pydantic models guarantees perfect schema
parity instead of two schemas drifting apart. A real backend team would of
course maintain their own independent schema that happens to satisfy this
same contract.

Each case's `documents` entry points at one of the 7 existing sample PDFs
in `Salary_Statement/` at the repo root (docs/SDD.md section 1.4), and
`customer.name` is deliberately set to either match or mismatch that PDF's
embedded employee name -- so this dataset doubles as a ready-made fixture
set for Stage 1 validation once it's implemented (case 4 is an intentional
name mismatch; the rest match exactly, per docs/SDD.md Design Decision D4).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from loan_restructuring_sdk.models.case_dto import (
    Case,
    Customer,
    DocumentRef,
    DocumentType,
    Loan,
    RestructuringRequest,
    RestructuringType,
)

MOCK_CASES: dict[int, Case] = {
    1: Case(
        id=1,
        application_number="APP-2026-0001",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 15, 9, 20, 0),
        updated_at=datetime(2026, 7, 18, 11, 5, 0),
        customer=Customer(
            id=101,
            name="Ahmed Mohammad Ali",
            national_id="9871234501",
            birth_date=date(1985, 3, 12),
            employer="Tech Corp Jordan",
            monthly_salary=Decimal("5175.00"),
            net_salary=Decimal("4500.00"),
            email="ahmed.ali@example.com",
            phone="0791234501",
        ),
        loan=Loan(
            id=201,
            account_number="ACC-100501",
            loan_type="PERSONAL",
            original_amount=Decimal("15000.00"),
            remaining_balance=Decimal("8200.00"),
            current_installment=Decimal("410.00"),
            interest_rate=Decimal("4.75"),
            term_months=36,
            loan_start_date=date(2024, 8, 1),
            loan_maturity_date=date(2027, 8, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(
            reason="فقدت جزءًا من دخلي بسبب تقليص ساعات العمل في الشركة وأحتاج لتخفيض القسط الشهري.",
            type=RestructuringType.DECREASE,
        ),
        documents=[
            DocumentRef(
                type=DocumentType.SALARY_STATEMENT,
                file="Salary_Statement/mock_data_test_case_1_pass.pdf",
            )
        ],
    ),
    2: Case(
        id=2,
        application_number="APP-2026-0002",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 14, 10, 0, 0),
        updated_at=datetime(2026, 7, 17, 13, 45, 0),
        customer=Customer(
            id=102,
            name="Ahmed Mohammad",
            national_id="9871234502",
            birth_date=date(1990, 6, 22),
            employer="Arab Bank PLC",
            monthly_salary=Decimal("5980.00"),
            net_salary=Decimal("5200.00"),
            email="ahmed.mohammad@example.com",
            phone="0791234502",
        ),
        loan=Loan(
            id=202,
            account_number="ACC-100502",
            loan_type="PERSONAL",
            original_amount=Decimal("12000.00"),
            remaining_balance=Decimal("5200.00"),
            current_installment=Decimal("300.00"),
            interest_rate=Decimal("4.50"),
            term_months=48,
            loan_start_date=date(2023, 11, 1),
            loan_maturity_date=date(2027, 11, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(
            reason="أرغب في سداد القرض بشكل أسرع بعد حصولي على ترقية وزيادة في الراتب.",
            type=RestructuringType.INCREASE,
        ),
        documents=[
            DocumentRef(
                type=DocumentType.SALARY_STATEMENT,
                file="Salary_Statement/mock_data_test_case_2_fuzzy_pass.pdf",
            )
        ],
    ),
    3: Case(
        id=3,
        application_number="APP-2026-0003",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 10, 8, 30, 0),
        updated_at=datetime(2026, 7, 16, 9, 15, 0),
        customer=Customer(
            id=103,
            name="Mohammad Hassan Ibrahim",
            national_id="9871234503",
            birth_date=date(1988, 1, 9),
            employer="Orange Jordan",
            monthly_salary=Decimal("4370.00"),
            net_salary=Decimal("3800.00"),
            email="mohammad.ibrahim@example.com",
            phone="0791234503",
        ),
        loan=Loan(
            id=203,
            account_number="ACC-100503",
            loan_type="PERSONAL",
            original_amount=Decimal("9000.00"),
            remaining_balance=Decimal("4100.00"),
            current_installment=Decimal("230.00"),
            interest_rate=Decimal("5.00"),
            term_months=40,
            loan_start_date=date(2024, 2, 1),
            loan_maturity_date=date(2027, 6, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(
            reason="تعرضت لوعكة صحية طارئة استلزمت نفقات علاج كبيرة وأحتاج لتخفيف الأعباء المالية الشهرية.",
            type=RestructuringType.DECREASE,
        ),
        documents=[
            DocumentRef(
                type=DocumentType.SALARY_STATEMENT,
                file="Salary_Statement/mock_data_test_case_3_old_month.pdf",
            )
        ],
    ),
    4: Case(
        id=4,
        application_number="APP-2026-0004",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 12, 14, 0, 0),
        updated_at=datetime(2026, 7, 19, 10, 30, 0),
        customer=Customer(
            id=104,
            # Deliberately different from the PDF's embedded employee name
            # ("Fatima Abdul Aziz") -- an intentional NAME_MISMATCH fixture
            # for Stage 1's exact-match identity rule (docs/SDD.md D4).
            name="Fatima Al-Zahra Odeh",
            national_id="9871234504",
            birth_date=date(1992, 11, 30),
            employer="Fastlink Ltd",
            monthly_salary=Decimal("4830.00"),
            net_salary=Decimal("4200.00"),
            email="fatima.odeh@example.com",
            phone="0791234504",
        ),
        loan=Loan(
            id=204,
            account_number="ACC-100504",
            loan_type="PERSONAL",
            original_amount=Decimal("13500.00"),
            remaining_balance=Decimal("6700.00"),
            current_installment=Decimal("350.00"),
            interest_rate=Decimal("4.75"),
            term_months=42,
            loan_start_date=date(2023, 9, 1),
            loan_maturity_date=date(2027, 3, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(
            reason="انخفض دخل الأسرة بعد تقاعد الزوج وأحتاج لإعادة جدولة القرض.",
            type=RestructuringType.DECREASE,
        ),
        documents=[
            DocumentRef(
                type=DocumentType.SALARY_STATEMENT,
                file="Salary_Statement/mock_data_test_case_4_name_mismatch.pdf",
            )
        ],
    ),
    5: Case(
        id=5,
        application_number="APP-2026-0005",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 8, 11, 10, 0),
        updated_at=datetime(2026, 7, 20, 16, 0, 0),
        customer=Customer(
            id=105,
            name="Omar Khalid Mahmoud",
            national_id="9871234505",
            birth_date=date(1979, 4, 17),
            employer="Global Finance Solutions",
            monthly_salary=Decimal("9775.00"),
            net_salary=Decimal("8500.00"),
            email="omar.mahmoud@example.com",
            phone="0791234505",
        ),
        loan=Loan(
            id=205,
            account_number="ACC-100505",
            loan_type="PERSONAL",
            original_amount=Decimal("25000.00"),
            remaining_balance=Decimal("14300.00"),
            current_installment=Decimal("650.00"),
            interest_rate=Decimal("4.25"),
            term_months=48,
            loan_start_date=date(2024, 1, 1),
            loan_maturity_date=date(2028, 1, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(
            reason="أواجه صعوبة مؤقتة بسبب التزامات عائلية طارئة وأحتاج لتخفيض القسط لبضعة أشهر.",
            type=RestructuringType.DECREASE,
        ),
        documents=[
            DocumentRef(
                type=DocumentType.SALARY_STATEMENT,
                file="Salary_Statement/mock_data_test_case_5_senior.pdf",
            )
        ],
    ),
    6: Case(
        id=6,
        application_number="APP-2026-0006",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 9, 13, 40, 0),
        updated_at=datetime(2026, 7, 19, 15, 20, 0),
        customer=Customer(
            id=106,
            name="Noor Jamal Karim",
            national_id="9871234506",
            birth_date=date(1996, 9, 5),
            employer="Jordan IT Consulting",
            monthly_salary=Decimal("3220.00"),
            net_salary=Decimal("2800.00"),
            email="noor.karim@example.com",
            phone="0791234506",
        ),
        loan=Loan(
            id=206,
            account_number="ACC-100506",
            loan_type="PERSONAL",
            original_amount=Decimal("7000.00"),
            remaining_balance=Decimal("3600.00"),
            current_installment=Decimal("190.00"),
            interest_rate=Decimal("5.25"),
            term_months=36,
            loan_start_date=date(2024, 5, 1),
            loan_maturity_date=date(2027, 5, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(
            reason="حصلت على دخل إضافي من عمل جزئي وأرغب في زيادة القسط لتقليل مدة القرض.",
            type=RestructuringType.INCREASE,
        ),
        documents=[
            DocumentRef(
                type=DocumentType.SALARY_STATEMENT,
                file="Salary_Statement/mock_data_test_case_6_junior.pdf",
            )
        ],
    ),
    7: Case(
        id=7,
        application_number="APP-2026-0007",
        status="UNDER_REVIEW",
        priority=None,
        created_at=datetime(2026, 7, 5, 8, 0, 0),
        updated_at=datetime(2026, 7, 20, 9, 0, 0),
        customer=Customer(
            id=107,
            name="Karim Rashed Nizar",
            national_id="9871234507",
            birth_date=date(1975, 12, 2),
            employer="Elite Business Group",
            monthly_salary=Decimal("14375.00"),
            net_salary=Decimal("12500.00"),
            email="karim.nizar@example.com",
            phone="0791234507",
        ),
        loan=Loan(
            id=207,
            account_number="ACC-100507",
            loan_type="PERSONAL",
            original_amount=Decimal("40000.00"),
            remaining_balance=Decimal("21000.00"),
            current_installment=Decimal("950.00"),
            interest_rate=Decimal("4.00"),
            term_months=60,
            loan_start_date=date(2023, 6, 1),
            loan_maturity_date=date(2028, 6, 1),
            loan_status="ACTIVE",
        ),
        restructuring_request=RestructuringRequest(
            reason="تأخرت عدة أقساط بسبب ظروف عمل طارئة وأحتاج لإعادة هيكلة القرض بالكامل.",
            type=RestructuringType.DECREASE,
        ),
        documents=[
            DocumentRef(
                type=DocumentType.SALARY_STATEMENT,
                file="Salary_Statement/mock_data_test_case_7_manager.pdf",
            )
        ],
    ),
}


def get_case(case_id: int) -> Case | None:
    """Return the mock Case for `case_id`, or `None` if no such mock case exists."""
    return MOCK_CASES.get(case_id)
