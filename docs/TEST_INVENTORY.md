# OpenIPE testing inventory

This inventory is intentionally maintained alongside the hardening suite so a
new façade operation or route is visible during review.

## Internal API operations

| Namespace | Public operations | Coverage |
| --- | --- | --- |
| `auth` | `initial_admin`, `login`, `logout`, `current_user`, `change_password` | `test_internal_auth.py`, `test_hardening_security.py` |
| `users` | `list`, `get`, `create`, `update` | `test_internal_users.py`, `test_hardening_security.py`, `test_hardening_internal_contracts.py` |
| `inbox` | `list`, `create`, `get`, `update`, `delete`, `process`, `archive`, `discard`, `create_task`, `create_project`, `create_habit` | `test_internal_inbox.py`, `test_productivity_scenarios.py`, `test_hardening_internal_contracts.py` |
| `goals` | `list`, `get`, `create`, `update`, `lifecycle`, `pause`, `resume`, `achieve`, `abandon`, `archive`, `associate`, `remove`, `associated_ids`, `evidence` | `test_internal_goals.py`, `test_internal_goal_associations.py`, `test_productivity_scenarios.py` |
| `projects` | `list`, `get`, `create`, `update`, `lifecycle`, `tasks`, `set_next_action`, `clear_next_action`, `progress`, `pause`, `resume`, `complete`, `cancel`, `archive` | `test_internal_projects_tasks.py`, `test_productivity_scenarios.py` |
| `tasks` | `list`, `create`, `get`, `update`, `lifecycle`, `complete`, `reopen`, `cancel` | `test_internal_projects_tasks.py`, `test_productivity_scenarios.py`, `test_hardening_internal_contracts.py` |
| `habits` | `list`, `get`, `create`, `update`, `lifecycle`, `check_in`, `get_check_in`, `recent_check_ins`, `delete_check_in`, `activate`, `deactivate`, `archive` | `test_internal_habits.py`, `test_productivity_scenarios.py` |
| `habit_stacks` | `list`, `get`, `create`, `update`, `lifecycle`, `add_habit`, `remove_habit`, `reorder_stacks`, `reorder_habits`, `unstacked`, `progress`, `archive` | `test_internal_habit_stacks.py`, `test_productivity_scenarios.py` |
| `today` | `get` | `test_internal_today.py`, `test_productivity_scenarios.py` |

The façade boundary is additionally checked for immutable contracts, context
requirements, ownership isolation, and absence of raw models/SQLite rows in
`test_hardening_internal_contracts.py`.

## REST route families

Authentication/setup and user administration are covered by
`test_api_auth.py`, `test_hardening_rest_http.py`, and
`test_rest_delegation.py`. Inbox, goals, projects, tasks, habits, stacks, and
Today route families are covered by their existing `test_api_*.py` modules,
the delegation tests, and the malformed-input/isolation cases in
`test_hardening_rest_http.py`. `test_rest_boundary.py` AST-parses every REST
module and rejects direct Core, application, persistence, and SQLite imports.

## Layers

- Core/security/configuration and persistence: `test_auth_service.py`,
  `test_foundation.py`, `test_hardening_foundation.py`,
  `test_hardening_security.py`, and repository/service tests.
- Application and internal workflows: `test_internal_*.py` and
  `test_productivity_scenarios.py`.
- HTTP adapter and contracts: `test_api_*.py`, `test_rest_*.py`, and
  `test_hardening_rest_http.py`.
- Restart and cross-model behavior: `test_productivity_scenarios.py`.

## Wave 2 exact operation matrix

The following is the review-level method inventory. Matrix tests are listed by
their exact parametrized test name; each parameter ID is a separate collected
case.

| Public operation(s) | Exact tests |
| --- | --- |
| `InternalAPI.authenticate`, `authorize_admin` | `test_internal_authentication_and_revocation`, `test_non_admin_cannot_read_or_mutate_administration`, `test_every_namespace_requires_an_internal_context` in `tests/test_wave2_internal_matrix.py` |
| `auth.initial_admin`, `login`, `logout`, `current_user`, `change_password` | `test_internal_authentication_and_revocation`, `test_initial_admin_and_password_change_are_internal`, `test_double_logout_and_unknown_tokens_are_authentication_errors`, `test_authentication_errors_do_not_echo_credentials` |
| `users.list`, `get`, `create`, `update` | `test_admin_user_operations_and_authorization`, `test_duplicate_usernames_are_case_insensitive_and_names_are_normalized`, `test_public_namespace_getters_return_internal_contracts[users-get]` |
| `inbox.list`, `create`, `get`, `update`, `delete` | `test_internal_inbox_accepts_and_normalizes_meaningful_text[*]`, `test_internal_inbox_status_filter_returns_only_requested_state[*]`, `test_internal_inbox_rejects_empty_text_without_mutation[*]`, `test_inbox_and_all_conversion_paths` |
| `inbox.process`, `archive`, `discard` | `test_internal_inbox_lifecycle_helpers_are_repeatable[process|archive|discard]`, `test_archive_discard_and_delete_are_soft_operations` |
| `inbox.create_task`, `create_project`, `create_habit` | `test_inbox_and_all_conversion_paths`, `test_capture_to_completed_project_preserves_links_and_progress`, `test_habit_establishment_workflow_survives_membership_mutations` |
| `goals.list`, `get`, `create`, `update` | `test_goal_lifecycle_and_evidence_contract`, `test_internal_goal_lifecycle_dispatch_has_no_partial_mutation[*]`, `test_public_namespace_getters_are_internal_contracts[goals-get]` |
| `goals.lifecycle`, `pause`, `resume`, `achieve`, `abandon`, `archive` | `test_internal_goal_lifecycle_dispatch_has_no_partial_mutation[pause|achieve|abandon|archive]`, `test_goal_lifecycle_and_evidence_contract` |
| `goals.associate`, `remove`, `associated_ids`, `evidence` | `test_goal_association_kinds_are_idempotent_and_removable[project|task|habit]`, `test_goal_backed_work_updates_evidence_and_today_context`, `test_cross_user_association_is_rejected` |
| `projects.list`, `get`, `create`, `update` | `test_project_progress_and_next_action_rules`, `test_capture_to_completed_project_preserves_links_and_progress`, `test_public_namespace_getters_return_internal_contracts[projects-get]` |
| `projects.lifecycle`, `pause`, `resume`, `complete`, `cancel`, `archive` | `test_capture_to_completed_project_preserves_links_and_progress`, `test_project_lifecycle_clears_next_action`, `test_real_root_app_supports_each_productivity_workflow_family[lifecycle-recovery]` |
| `projects.tasks`, `progress`, `set_next_action`, `clear_next_action` | `test_project_progress_and_next_action_rules`, `test_project_task_progress_and_next_action_api`, `test_capture_to_completed_project_preserves_links_and_progress` |
| `tasks.list`, `create`, `get`, `update` | `test_internal_task_priority_round_trips_as_enum[*]`, `test_contract_input_fields_survive_round_trip_and_explicit_null_clears_values`, `test_public_namespace_getters_return_internal_contracts[tasks-get]` |
| `tasks.lifecycle`, `complete`, `reopen`, `cancel` | `test_internal_task_terminal_states_clear_or_preserve_expected_fields[*]`, `test_task_lifecycle_and_project_moves_clear_next_action`, `test_rest_repeated_lifecycle_requests_preserve_domain_errors` |
| `habits.list`, `get`, `create`, `update` | `test_internal_habit_schedule_matrix_accepts_valid_boundaries[*]`, `test_internal_habit_schedule_matrix_rejects_invalid_boundaries[*]`, `test_public_namespace_getters_return_internal_contracts[habits-get]` |
| `habits.lifecycle`, `activate`, `deactivate`, `archive` | `test_habit_update_activation_archive_and_minimum_version`, `test_habit_establishment_workflow_survives_membership_mutations` |
| `habits.check_in`, `get_check_in`, `recent_check_ins`, `delete_check_in` | `test_internal_checkin_status_upsert_and_lookup[*]`, `test_internal_checkin_history_limits_are_safe[*]`, `test_checkin_upsert_history_and_delete` |
| `habit_stacks.list`, `get`, `create`, `update` | `test_stack_reorder_preserves_exact_membership_and_positions[*]`, `test_public_namespace_getters_return_internal_contracts[habit-stacks-get]` |
| `habit_stacks.lifecycle`, `archive`, `add_habit`, `remove_habit` | `test_stack_membership_ordering_and_unstacked_query`, `test_archived_stack_cannot_receive_habits`, `test_habit_establishment_workflow_survives_membership_mutations` |
| `habit_stacks.reorder_stacks`, `reorder_habits`, `unstacked`, `progress` | `test_stack_reorder_preserves_exact_membership_and_positions[*]`, `test_stack_reorder_rejects_non_exact_sets_without_mutation[*]`, `test_stack_membership_order_progress_and_reorder_api` |
| `today.get` | `test_today_contract_matrix_is_date_stable_and_complete[*]`, `test_daily_execution_loop_tracks_stacks_unstacked_habits_and_overdue_tasks`, `test_public_namespace_getters_return_internal_contracts[today-get]` |

## Wave 2 exact REST route coverage

Real ASGI contract coverage is in `tests/test_wave2_rest_matrix.py` and
`tests/test_wave2_public_inventory.py`; delegation-only coverage remains in
`tests/test_rest_delegation.py`. The route function inventory is:

| Route family | Route handlers covered |
| --- | --- |
| Setup/auth | `create_initial_admin`, `login`, `logout`, `current_user`, `change_password` |
| Users | `list_users`, `create_user`, `get_user`, `update_user` |
| Inbox | `list_inbox`, `create_inbox_item`, `get_inbox_item`, `update_inbox_item`, `delete_inbox_item`, `create_task_from_inbox`, `create_project_from_inbox`, `create_habit_from_inbox` |
| Goals | `list_goals`, `create_goal`, `get_goal`, `update_goal`, `associate_project`, `remove_project`, `associate_task`, `remove_task`, `associate_habit`, `remove_habit` |
| Projects | `list_projects`, `create_project`, `get_project`, `update_project`, `project_tasks`, `set_next_action`, `clear_next_action` |
| Tasks | `list_tasks`, `create_task`, `get_task`, `update_task`, `lifecycle` |
| Habits/check-ins | `list_habits`, `create_habit`, `get_habit`, `update_habit`, `check_in`, `recent_check_ins`, `delete_check_in` |
| Habit stacks | `list_stacks`, `create_stack`, `get_stack`, `update_stack`, `reorder_stacks`, `reorder_habits`, `add_habit`, `remove_habit` |
| Today | `today` |

The AST boundary suite is `test_rest_has_no_core_application_or_persistence_imports`,
`test_rest_does_not_read_internal_implementation_details`, and
`test_rest_dependency_does_not_expose_connection` in
`tests/test_rest_boundary.py`.

Focused adapter delegation is covered by
`test_each_rest_family_delegates_exactly_once_with_opaque_context[*]` in
`tests/test_wave2_delegation.py`, with separate cases for auth, users, Inbox,
goals, projects, tasks, habits, habit stacks, and Today.

## Wave 3 enforcement and persistence evidence

`tests/coverage_registry.py` is the machine-readable registry. The meta-tests
in `tests/test_wave3_registries.py` compare its internal operation surface to
the live façade implementation and its REST path surface to `app.openapi()`.
Every registered REST path declares exact success and failure test references.

Direct repository evidence is in `tests/test_wave3_persistence.py`, covering
owner predicates, association idempotency and cleanup, nullable round trips,
filters, foreign keys, commit visibility, and SQLite invariants.

The deterministic state-machine matrix is in
`tests/test_wave3_state_machines.py`. Genuine file-backed root-factory restart
scenarios are in `tests/test_wave3_restart.py`; they use the root app, real
HTTP clients, persisted authentication, and owned-lifespan shutdown before
reconstruction.

Wave 3 route-level references:

| Surface | Exact coverage |
| --- | --- |
| FastAPI path registry | `test_rest_registry_matches_every_concrete_fastapi_path` |
| Internal operation registry | `test_internal_registry_contains_all_public_methods_on_a_real_facade` |
| Root restart scenarios | `test_root_app_restart_preserves_committed_productivity_state[*]`, `test_root_owned_connection_is_closed_after_real_lifespan` |
| Repository invariants | All parameterized cases in `test_wave3_persistence.py` |
| Lifecycle and progress invariants | All parameterized cases in `test_wave3_state_machines.py` |
| Contract-field atomicity | `test_each_create_contract_produces_the_expected_public_shape[*]`, `test_update_fields_are_independently_observable[*]`, `test_failed_internal_operation_leaves_public_state_unchanged[*]` |
