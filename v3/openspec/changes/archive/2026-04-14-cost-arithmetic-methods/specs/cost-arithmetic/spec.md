## ADDED Requirements

### Requirement: Cost supports addition
The system SHALL support adding two `Cost` instances with the `+` operator, returning a new `Cost` whose fields are the element-wise sums. `Cost.__radd__` SHALL accept `int` 0 so that `sum(costs, Cost())` works.

#### Scenario: Adding two non-zero costs
- **WHEN** `Cost(mp=1, cp=2, xp=3, ip=4) + Cost(mp=10, cp=20, xp=30, ip=40)` is evaluated
- **THEN** the result is `Cost(mp=11, cp=22, xp=33, ip=44)`

#### Scenario: Adding a zero Cost acts as identity
- **WHEN** any `Cost` is added to `Cost()` (all zeros)
- **THEN** the result equals the original `Cost`

#### Scenario: sum() over a list of Costs
- **WHEN** `sum([Cost(mp=1), Cost(mp=2), Cost(cp=5)], Cost())` is evaluated
- **THEN** the result is `Cost(mp=3, cp=5)`

### Requirement: Cost supports scalar multiplication
The system SHALL support multiplying a `Cost` by a non-negative `int` with `cost * n` and `n * cost`, returning a new `Cost` whose fields are each multiplied by `n`.

#### Scenario: Multiplying a cost by a positive integer
- **WHEN** `Cost(mp=3, cp=1, xp=0, ip=2) * 4` is evaluated
- **THEN** the result is `Cost(mp=12, cp=4, xp=0, ip=8)`

#### Scenario: Reflected multiplication is equivalent
- **WHEN** `4 * Cost(mp=3, cp=1, xp=0, ip=2)` is evaluated
- **THEN** the result equals `Cost(mp=3, cp=1, xp=0, ip=2) * 4`

#### Scenario: Multiplying by zero yields a zero Cost
- **WHEN** any `Cost` is multiplied by `0`
- **THEN** the result is `Cost()` (all fields zero)

### Requirement: Cost can convert itself to points
The system SHALL provide a `to_points()` method on `Cost` that returns `int` equal to `mp + cp + xp + 3 * ip`.

#### Scenario: Standard points formula
- **WHEN** `Cost(mp=2, cp=3, xp=1, ip=2).to_points()` is called
- **THEN** the result is `2 + 3 + 1 + 3*2 = 12`

#### Scenario: Zero cost yields zero points
- **WHEN** `Cost().to_points()` is called
- **THEN** the result is `0`
