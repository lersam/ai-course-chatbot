---
name: refactor
description: 'Surgical code refactoring to improve maintainability without changing behavior. Covers extracting functions, renaming variables, breaking down god functions, improving type safety, eliminating code smells, and applying design patterns. Less drastic than repo-rebuilder; use for gradual improvements.'
license: MIT
---

# Refactor

## Overview

Improve code structure and readability without changing external behavior. Refactoring is gradual evolution, not revolution. Use this for improving existing code, not rewriting from scratch.

## When to Use

Use this skill when:

- Code is hard to understand or maintain
- Functions/classes are too large
- Code smells need addressing
- Adding features is difficult due to code structure
- User asks "clean up this code", "refactor this", "improve this"

## Before Making Changes
Before editing, modifying, or deleting any code, you must:

1. Present a numbered list of every file you intend to edit, modify, or delete
2. For each file, show a snapshot of tha relevant code sections you intend to change, with line numbers.
3. Briefly describe the planned change for each item (edit, modify, or delete) and why.
4. **Ask for explicit approval to proceed** after presenting the above information.
---

## Refactoring Principles

### The Golden Rules

1. **Behavior is preserved** - Refactoring doesn't change what the code does, only how
2. **Small steps** - Make tiny changes, test after each
3. **Version control is your friend** - Commit before and after each safe state
4. **Tests are essential** - Without tests, you're not refactoring, you're editing
5. **One thing at a time** - Don't mix refactoring with feature changes

### When NOT to Refactor

```
- Code that works and won't change again (if it ain't broke...)
- Critical production code without tests (add tests first)
- When you're under a tight deadline
- "Just because" - need a clear purpose
```

<!-- Insert Python-specific engineering rules that align with the repository standards -->

### Python-specific Rules

These are repository-level, non-negotiable guidelines to use while refactoring Python code examples and suggestions in this skill. They reflect the engineering standards used across this repository.

- Use Python 3.10+ type hints everywhere in public APIs (e.g. `str | None`, `list[str]`).
- Prefer immutable dataclasses for domain/config models: `@dataclass(frozen=True)`; validate invariants in `__post_init__` only.
- Use `logging` for runtime diagnostics. Create a module-level logger: `logger = logging.getLogger(__name__)` and use `%`-style placeholders in log messages, e.g. `logger.info("Processed %s records", count)`; use `logger.exception(...)` to log exceptions with tracebacks. Never use `print` for runtime diagnostics.
- Use `pathlib.Path` for filesystem operations and f-strings for non-logging string formatting.
- Avoid mutable module-level state; constants must be uppercase and typed.
- Keep business logic pure and side-effect-free where possible; isolate I/O at boundaries.
- Use `async def` for I/O-bound operations and prefer async-first handlers for frameworks like FastAPI.
- Use `pytest` with fixtures for tests; do not connect tests to production databases (use in-memory SQLite or StaticPool for SQLAlchemy tests).
- For external schema parsing (API boundaries) only, use `pydantic.BaseModel` with strict config; otherwise prefer dataclasses.
- Every public module, class, and function must include a concise docstring describing purpose, side effects, and high-level error behavior.

<!-- End inserted rules -->

---

## Common Code Smells & Fixes

### 1. Long Method/Function

```diff
- # BAD: One long function that does everything (Python example)
- async def process_order(order_id: str):
-     # fetch order
-     order = await fetch_order(order_id)
-     # validate
-     if not order:
-         raise ValueError("order not found")
-     # calculate pricing
-     pricing = calculate_pricing(order)
-     # update inventory
-     await update_inventory(order)
-     # create shipment
-     shipment = await create_shipment(order)
-     # send notifications
-     await send_notifications(order, pricing, shipment)
-     return {"order": order, "pricing": pricing, "shipment": shipment}
+ # GOOD: Broken into focused functions
+ async def process_order(order_id: str) -> dict:
+     order = await fetch_order(order_id)
+     validate_order(order)
+     pricing = calculate_pricing(order)
+     await update_inventory(order)
+     shipment = await create_shipment(order)
+     await send_notifications(order, pricing, shipment)
+     return {"order": order, "pricing": pricing, "shipment": shipment}
```

### 2. Duplicated Code

```diff
- # BAD: Same logic in multiple places
- def calculate_user_discount(user: User) -> float:
-     if user.membership == 'gold':
-         return user.total * 0.2
-     if user.membership == 'silver':
-         return user.total * 0.1
-     return 0.0
-
- def calculate_order_discount(order: Order) -> float:
-     if order.user.membership == 'gold':
-         return order.total * 0.2
-     if order.user.membership == 'silver':
-         return order.total * 0.1
-     return 0.0
+ # GOOD: Extract common logic
+ def get_membership_discount_rate(membership: str) -> float:
+     rates: dict[str, float] = {"gold": 0.2, "silver": 0.1}
+     return rates.get(membership, 0.0)
+
+ def calculate_user_discount(user: 'User') -> float:
+     return user.total * get_membership_discount_rate(user.membership)
+
+ def calculate_order_discount(order: 'Order') -> float:
+     return order.total * get_membership_discount_rate(order.user.membership)
```

### 3. Large Class/Module

```diff
- # BAD: God object that knows too much
- class UserManager:
-     def create_user(self, data): ...
-     def update_user(self, id, data): ...
-     def delete_user(self, id): ...
-     def send_email(self, *args, **kwargs): ...
-     def generate_report(self): ...
-     def handle_payment(self): ...
-     def validate_address(self, address): ...
-
+ # GOOD: Single responsibility per class (Python services)
+ from dataclasses import dataclass
+
+ @dataclass(frozen=True)
+ class UserService:
+     """Service responsible for CRUD operations on users."""
+
+     def create(self, data: dict) -> 'User': ...
+     def update(self, user_id: str, data: dict) -> 'User': ...
+     def delete(self, user_id: str) -> None: ...
+
+ class EmailService:
+     def send(self, to: str, subject: str, body: str) -> None: ...
+
+ class ReportService:
+     def generate(self, type_: str, params: dict) -> dict: ...
+
+ class PaymentService:
+     def process(self, amount: float, method: str) -> dict: ...
```

### 4. Long Parameter List

```diff
- # BAD: Too many parameters
- def create_user(email, password, name, age, address, city, country, phone):
-     pass
-
+ # GOOD: Group related parameters using dataclass
+ from dataclasses import dataclass
+
+ @dataclass(frozen=True)
+ class Address:
+     street: str
+     city: str
+     country: str
+
+ @dataclass(frozen=True)
+ class UserData:
+     email: str
+     password: str
+     name: str
+     age: int | None = None
+     address: Address | None = None
+     phone: str | None = None
+
+ def create_user(data: UserData) -> 'User':
+     """Create a user from a grouped parameter object."""
+     ...
```

### 5. Feature Envy

```diff
- # BAD: Method that uses another object's data more than its own
- class Order:
-     def calculate_discount(self, user):
-         if user.membership_level == 'gold':
-             return self.total * 0.2
-         if user.account_age > 365:
-             return self.total * 0.1
-         return 0
-
+ # GOOD: Move logic to the object that owns the data
+ @dataclass(frozen=True)
+ class User:
+     membership_level: str
+     account_age: int
+
+     def get_discount_rate(self, order_total: float) -> float:
+         if self.membership_level == 'gold':
+             return 0.2
+         if self.account_age > 365:
+             return 0.1
+         return 0.0
+
+ @dataclass(frozen=True)
+ class Order:
+     total: float
+
+     def calculate_discount(self, user: User) -> float:
+         return self.total * user.get_discount_rate(self.total)
```

### 6. Primitive Obsession

```diff
- # BAD: Using primitives for domain concepts
- def send_email(to, subject, body):
-     pass
-
- def create_phone(country, number):
-     return f"{country}-{number}"
-
+ # GOOD: Use domain types (value objects)
+ from dataclasses import dataclass
+
+ @dataclass(frozen=True)
+ class Email:
+     """Immutable email value object with validation."""
+     value: str
+
+     def __post_init__(self) -> None:
+         if '@' not in self.value:
+             raise ValueError('Invalid email')
+
+ @dataclass(frozen=True)
+ class PhoneNumber:
+     country: str
+     number: str
+
+     def __post_init__(self) -> None:
+         if not self.number:
+             raise ValueError('Invalid phone')
+
+     def __str__(self) -> str:
+         return f"{self.country}-{self.number}"
```

### 7. Magic Numbers/Strings

```diff
- # BAD: Unexplained values
- if user.status == 2:
-     pass
- discount = total * 0.15
- sleep(86400)
-
+ # GOOD: Named constants
+ from enum import IntEnum
+
+ class UserStatus(IntEnum):
+     ACTIVE = 1
+     INACTIVE = 2
+     SUSPENDED = 3
+
+ DISCOUNT_RATES: dict[str, float] = {
+     "STANDARD": 0.1,
+     "PREMIUM": 0.15,
+     "VIP": 0.2,
+ }
+
+ ONE_DAY_SECONDS = 24 * 60 * 60
+
+ if user.status == UserStatus.INACTIVE:
+     ...
```

### 8. Nested Conditionals

```diff
- # BAD: Deeply nested checks
- def process(order):
-     if order:
-         if order.user:
-             if order.user.is_active:
-                 if order.total > 0:
-                     return process_order(order)
-                 else:
-                     return {"error": "Invalid total"}
-             else:
-                 return {"error": "User inactive"}
-         else:
-             return {"error": "No user"}
-     else:
-         return {"error": "No order"}
-
+ # GOOD: Guard clauses / early returns
+ def process(order: dict) -> dict:
+     if not order:
+         return {"error": "No order"}
+     if not order.get("user"):
+         return {"error": "No user"}
+     if not order["user"].get("is_active"):
+         return {"error": "User inactive"}
+     if order.get("total", 0) <= 0:
+         return {"error": "Invalid total"}
+     return process_order(order)
```

### 9. Dead Code

```diff
- # BAD: Unused code lingers
- def old_implementation():
-     pass
- DEPRECATED_VALUE = 5
- # commented-out code
-
+ # GOOD: Remove unused code; rely on version control to restore if needed
+ # Delete unused functions, imports, and commented code. Keep tests green.
```

### 10. Inappropriate Intimacy

```diff
- # BAD: One class reaches deep into another
- class OrderProcessor:
-     def process(self, order):
-         _ = order.user.profile.address.street  # too intimate
-
+ # GOOD: Ask, don't tell — prefer encapsulation
+ class OrderProcessor:
+     def process(self, order: 'Order') -> None:
+         shipping_address = order.get_shipping_address()
+         order.save()
```

---

## Extract Method Refactoring

### Before and After

```diff
- # Before: One long function (JS example) — replaced with a Python example
- def print_report(users):
-     print('USER REPORT')
-     print('============')
-     print()
-     print(f'Total users: {len(users)}')
-     print()
-     print('ACTIVE USERS')
-     print('------------')
-     active = [u for u in users if u.is_active]
-     for u in active:
-         print(f'- {u.name} ({u.email})')
-     print()
-     print(f'Active: {len(active)}')
-     print()
-     print('INACTIVE USERS')
-     print('--------------')
-     inactive = [u for u in users if not u.is_active]
-     for u in inactive:
-         print(f'- {u.name} ({u.email})')
-     print()
-     print(f'Inactive: {len(inactive)}')
-
+ # After: Extracted methods following repository standards
+ import logging
+ from dataclasses import dataclass
+ from typing import Iterable, List
+
+ logger = logging.getLogger(__name__)
+
+ @dataclass(frozen=True)
+ class User:
+     """Immutable user DTO used for reports."""
+     name: str
+     email: str
+     is_active: bool
+
+ def print_report(users: Iterable[User]) -> None:
+     """Log a user report. Side effects: emits structured logs. Errors: logs unexpected issues."""
+     users_list: List[User] = list(users)
+     _print_header('USER REPORT')
+     logger.info('Total users: %s', len(users_list))
+     _print_user_section('ACTIVE USERS', [u for u in users_list if u.is_active])
+     _print_user_section('INACTIVE USERS', [u for u in users_list if not u.is_active])
+
+ def _print_header(title: str) -> None:
+     """Log a formatted section header."""
+     line = '=' * len(title)
+     logger.info('%s', title)
+     logger.info('%s', line)
+     logger.info('')
+
+ def _print_user_section(title: str, users: Iterable[User]) -> None:
+     """Log a user subsection and a count."""
+     users_list = list(users)
+     logger.info('%s', title)
+     logger.info('%s', '-' * len(title))
+     for u in users_list:
+         logger.info('- %s (%s)', u.name, u.email)
+     logger.info('')
+     logger.info('%s: %s', title.split()[0], len(users_list))
+     logger.info('')
```

---

## Introducing Type Safety

```diff
- # Before: No types (JS example)
- function calculateDiscount(user, total, membership, date) { }
-
+ # After: Full type safety (Python dataclasses + type hints)
+ from dataclasses import dataclass
+ from typing import TypedDict
+ from datetime import date
+
+ @dataclass(frozen=True)
+ class User:
+     id: str
+     name: str
+     membership: str
+
+ @dataclass(frozen=True)
+ class DiscountResult:
+     original: float
+     discount: float
+     final: float
+     rate: float
+
+ def calculate_discount(user: User, total: float, when: date | None = None) -> DiscountResult:
+     """Calculate discount with explicit types and validation.
+
+     Raises ValueError for invalid inputs.
+     """
+     when = when or date.today()
+     if total < 0:
+         raise ValueError('Total cannot be negative')
+
+     rate = 0.1  # default bronze
+     if user.membership == 'gold' and when.weekday() == 4:  # Friday
+         rate = 0.25
+     elif user.membership == 'gold':
+         rate = 0.2
+     elif user.membership == 'silver':
+         rate = 0.15
+
+     discount = total * rate
+     return DiscountResult(original=total, discount=discount, final=total - discount, rate=rate)
```

---

## Design Patterns for Refactoring

### Strategy Pattern

```diff
- # Before: Conditional logic (JS)
- function calculateShipping(order, method) { ... }
-
+ # After: Strategy pattern (Python)
+ from abc import ABC, abstractmethod
+ from dataclasses import dataclass
+
+ class ShippingStrategy(ABC):
+     @abstractmethod
+     def calculate(self, order: 'Order') -> float:
+         pass
+
+ class StandardShipping(ShippingStrategy):
+     def calculate(self, order: 'Order') -> float:
+         return 0.0 if order.total > 50 else 5.99
+
+ class ExpressShipping(ShippingStrategy):
+     def calculate(self, order: 'Order') -> float:
+         return 9.99 if order.total > 100 else 14.99
+
+ class OvernightShipping(ShippingStrategy):
+     def calculate(self, order: 'Order') -> float:
+         return 29.99
+
+ def calculate_shipping(order: 'Order', strategy: ShippingStrategy) -> float:
+     return strategy.calculate(order)
```

### Chain of Responsibility

```diff
- # Before: Nested validation (JS)
- function validate(user) { ... }
-
+ # After: Chain of responsibility (Python)
+ from typing import Optional
+
+ class Validator(ABC):
+     def __init__(self) -> None:
+         self._next: Optional['Validator'] = None
+
+     def set_next(self, validator: 'Validator') -> 'Validator':
+         self._next = validator
+         return validator
+
+     def validate(self, user: 'User') -> Optional[str]:
+         error = self.do_validate(user)
+         if error:
+             return error
+         if self._next:
+             return self._next.validate(user)
+         return None
+
+     @abstractmethod
+     def do_validate(self, user: 'User') -> Optional[str]:
+         ...
+
+ class EmailRequiredValidator(Validator):
+     def do_validate(self, user: 'User') -> Optional[str]:
+         return 'Email required' if not getattr(user, 'email', None) else None
+
+ class EmailFormatValidator(Validator):
+     def do_validate(self, user: 'User') -> Optional[str]:
+         email = getattr(user, 'email', None)
+         return 'Invalid email' if email and '@' not in email else None
+
+ # Build the chain
+ validator = EmailRequiredValidator()
+ validator.set_next(EmailFormatValidator())
```

---

## Refactoring Steps

### Safe Refactoring Process

```
1. PREPARE
   - Ensure tests exist (write them if missing)
   - Commit current state
   - Create feature branch

2. IDENTIFY
   - Find the code smell to address
   - Understand what the code does
   - Plan the refactoring

3. REFACTOR (small steps)
   - Make one small change
   - Run tests
   - Commit if tests pass
   - Repeat

4. VERIFY
   - All tests pass
   - Manual testing if needed
   - Performance unchanged or improved

5. CLEAN UP
   - Update comments
   - Update documentation
   - Final commit
```

---

## Refactoring Checklist

### Code Quality

- [ ] Functions are small (< 50 lines)
- [ ] Functions do one thing
- [ ] No duplicated code
- [ ] Descriptive names (variables, functions, classes)
- [ ] No magic numbers/strings
- [ ] Dead code removed

### Structure

- [ ] Related code is together
- [ ] Clear module boundaries
- [ ] Dependencies flow in one direction
- [ ] No circular dependencies

### Type Safety

- [ ] Types defined for all public APIs
- [ ] No `any` types without justification
- [ ] Nullable types explicitly marked

### Testing

- [ ] Refactored code is tested
- [ ] Tests cover edge cases
- [ ] All tests pass

---

## Common Refactoring Operations

| Operation                                     | Description                           |
| --------------------------------------------- | ------------------------------------- |
| Extract Method                                | Turn code fragment into method        |
| Extract Class                                 | Move behavior to new class            |
| Extract Interface                             | Create interface from implementation  |
| Inline Method                                 | Move method body back to caller       |
| Inline Class                                  | Move class behavior to caller         |
| Pull Up Method                                | Move method to superclass             |
| Push Down Method                              | Move method to subclass               |
| Rename Method/Variable                        | Improve clarity                       |
| Introduce Parameter Object                    | Group related parameters              |
| Replace Conditional with Polymorphism         | Use polymorphism instead of switch/if |
| Replace Magic Number with Constant            | Named constants                       |
| Decompose Conditional                         | Break complex conditions              |
| Consolidate Conditional                       | Combine duplicate conditions          |
| Replace Nested Conditional with Guard Clauses | Early returns                         |
| Introduce Null Object                         | Eliminate null checks                 |
| Replace Type Code with Class/Enum             | Strong typing                         |
| Replace Inheritance with Delegation           | Composition over inheritance          |

