"""The transport-independent OpenIPE façade.

Resource namespaces intentionally live behind one façade so REST and local
clients share exactly the same authentication, ownership, and service rules.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any

from openipe.application.auth_service import AuthService
from openipe.application.goal_service import GoalService, UNSET as GOAL_UNSET
from openipe.application.habit_service import HabitService, UNSET as HABIT_UNSET
from openipe.application.habit_stack_service import HabitStackService, UNSET as STACK_UNSET
from openipe.application.inbox_service import InboxService
from openipe.application.project_service import ProjectService, UNSET as PROJECT_UNSET
from openipe.application.task_service import TaskService, UNSET as TASK_UNSET
from openipe.application.today_service import TodayService
from openipe.core.config import Settings
from openipe.core.models.user import User
from openipe.core.errors import AuthenticationError, InactiveUserError, NotFoundError, PermissionDeniedError, ValidationError

from .context import InternalContext
from .contracts import (
    ChangePasswordContract, CheckInContract, CheckInCreateContract, CredentialsContract,
    GoalContract, GoalCreateContract, GoalEvidenceContract,
    GoalUpdateContract, HabitContract, HabitCreateContract, HabitStackContract, HabitUpdateContract, InboxContract,
    InboxCreateContract, InboxHabitConversionContract, InboxTaskConversionContract, InboxUpdateContract, InitialAdminContract,
    LoginContract, ProjectContract, ProjectCreateContract, ProjectUpdateContract, ReorderContract,
    StackCreateContract, StackUpdateContract,
    TaskContract, TaskCreateContract, TaskUpdateContract, TodayCompletedContract, TodayContract, TodayGoalContract,
    TodayHabitContract, TodayProjectContract, TodayQueryContract, TodayStackContract, TodayTaskContract, UserContract,
    UserCreateContract, UserUpdateContract,
)
from .errors import (
    InvalidContextError,
    InternalAuthenticationError, InternalInactiveUserError, InternalNotFoundError,
    InternalPermissionDeniedError, InternalValidationError,
)


def _user(user: User) -> UserContract:
    return UserContract(user.id, user.username, user.display_name, user.is_admin,
                        user.is_active, user.created_at, user.updated_at, user.last_login_at)


def _inbox(item) -> InboxContract:
    return InboxContract(item.id, item.text, item.status, item.created_at, item.updated_at,
                         item.processed_at, item.archived_at)


def _task(item) -> TaskContract:
    return TaskContract(item.id, item.title, item.description, item.project_id, item.status,
                        item.priority, item.due_date, item.is_today, item.source_inbox_item_id,
                        item.created_at, item.updated_at, item.completed_at, item.archived_at)


def _habit(item) -> HabitContract:
    return HabitContract(item.id, item.title, item.description, item.frequency_type,
                         dict(item.frequency_config), item.minimum_version, item.stack_id,
                         item.position, item.active, item.source_inbox_item_id, item.created_at,
                         item.updated_at, item.archived_at)


def _checkin(item) -> CheckInContract:
    return CheckInContract(item.id, item.habit_id, item.date, item.status, item.note,
                           item.created_at, item.updated_at)


class AuthNamespace:
    """Unauthenticated login/setup and authenticated account operations."""
    def __init__(self, api): self.api = api
    def initial_admin(self, username, display_name=None, password=None):
        if isinstance(username, InitialAdminContract):
            username, display_name, password = username.username, username.display_name, username.password
        return _user(self.api.auth_service.create_initial_admin(username, display_name, password))
    def login(self, username, password=None):
        if isinstance(username, CredentialsContract):
            username, password = username.username, username.password
        user, token, expires = self.api.auth_service.login(username, password)
        return LoginContract(token, expires, _user(user))
    def logout(self, access_token): self.api.auth_service.logout(access_token)
    def current_user(self, context): return _user(context.actor)
    def change_password(self, context, current_password, new_password=None):
        if isinstance(current_password, ChangePasswordContract):
            current_password, new_password = current_password.current_password, current_password.new_password
        return self.api.auth_service.change_password(context.actor, current_password, new_password)


class UsersNamespace:
    """Administrator-only user management for REST and future local clients."""
    def __init__(self, api): self.api = api
    def list(self, context): return [_user(x) for x in self.api.auth_service.list_users(context.actor)]
    def get(self, context, user_id): return _user(self.api.auth_service.get_user(context.actor, user_id))
    def create(self, context, username, display_name=None, password=None, is_admin=False):
        if isinstance(username, UserCreateContract):
            request = username
            username, display_name, password, is_admin = request.username, request.display_name, request.password, request.is_admin
        return _user(self.api.auth_service.create_user(context.actor, username, display_name, password, is_admin))
    def update(self, context, user_id, display_name=None, is_active=None):
        if isinstance(display_name, UserUpdateContract):
            request = display_name
            display_name = request.display_name if "display_name" in request.provided else None
            is_active = request.is_active if "is_active" in request.provided else None
        target = self.api.auth_service.get_user(context.actor, user_id)
        if display_name is not None:
            if not display_name.strip():
                from openipe.core.errors import ValidationError
                raise ValidationError("Display name must not be empty")
            self.api.auth_service.users.update_display_name(user_id, display_name.strip())
        if is_active is not None:
            target = self.api.auth_service.set_active(context.actor, user_id, is_active)
        return _user(self.api.auth_service.get_user(context.actor, user_id))


class InboxNamespace:
    """Inbox capture, processing, and conversion operations."""
    def __init__(self, api): self.api = api
    def list(self, c, status=None): return [_inbox(x) for x in self.api.inbox_service.list(c.actor.id, status)]
    def create(self, c, text):
        if isinstance(text, InboxCreateContract):
            text = text.text
        return _inbox(self.api.inbox_service.create(c.actor.id, text))
    def get(self, c, item_id): return _inbox(self.api.inbox_service.get(c.actor.id, item_id))
    def update(self, c, item_id, text=None, status=None):
        if isinstance(text, InboxUpdateContract):
            text, status = text.text, text.status
        return _inbox(self.api.inbox_service.update(c.actor.id, item_id, text, status))
    def delete(self, c, item_id): return _inbox(self.api.inbox_service.delete(c.actor.id, item_id))
    def process(self, c, item_id):
        from openipe.core.models.inbox import InboxStatus
        return self.update(c, item_id, status=InboxStatus.PROCESSED)
    def archive(self, c, item_id):
        from openipe.core.models.inbox import InboxStatus
        return self.update(c, item_id, status=InboxStatus.ARCHIVED)
    def discard(self, c, item_id):
        from openipe.core.models.inbox import InboxStatus
        return self.update(c, item_id, status=InboxStatus.DISCARDED)
    def create_task(self, c, item_id, description=None, project_id=None, priority=None, due_date=None, is_today=False):
        if isinstance(description, InboxTaskConversionContract):
            request = description
            description, project_id, priority, due_date, is_today = request.description, request.project_id, request.priority, request.due_date, request.is_today
        item = self.api.inbox_service.get(c.actor.id, item_id)
        kwargs = {} if priority is None else {"priority": priority}
        task = self.api.tasks.create(c, item.text, description, project_id, due_date=due_date,
                                     is_today=is_today, source_inbox_item_id=item.id, **kwargs)
        return task
    def create_project(self, c, item_id, description=None):
        item = self.api.inbox_service.get(c.actor.id, item_id)
        return self.api.projects.create(c, item.text, description, item.id)
    def create_habit(self, c, item_id, description=None, frequency_type=None, frequency_config=None, minimum_version=None):
        if isinstance(description, InboxHabitConversionContract):
            request = description
            description, frequency_type, frequency_config, minimum_version = request.description, request.frequency_type, request.frequency_config, request.minimum_version
        item = self.api.inbox_service.get(c.actor.id, item_id)
        return self.api.habits.create(c, item.text, description, frequency_type, frequency_config,
                                      minimum_version, item.id)


class GoalsNamespace:
    """Goal lifecycle, evidence, and association operations."""
    def __init__(self, api): self.api = api
    def _result(self, c, goal):
        ids = self.associated_ids(c, goal.id); e = self.evidence(c, goal.id)
        return GoalContract(goal.id, goal.title, goal.description, goal.status, goal.target_date,
                            goal.created_at, goal.updated_at, goal.achieved_at, goal.archived_at,
                            goal.source_inbox_item_id, ids["project_ids"], ids["task_ids"], ids["habit_ids"],
                            GoalEvidenceContract(**e))
    def list(self,c,status=None): return [self._result(c,x) for x in self.api.goal_service.list(c.actor.id,status)]
    def get(self,c,id): return self._result(c,self.api.goal_service.get(c.actor.id,id))
    def create(self,c,title,description=None,target_date=None,source_inbox_item_id=None):
        if isinstance(title, GoalCreateContract):
            request = title
            title, description, target_date, source_inbox_item_id = request.title, request.description, request.target_date, request.source_inbox_item_id
        return self._result(c,self.api.goal_service.create(c.actor.id,title,description,target_date,source_inbox_item_id))
    def update(self,c,id,title=GOAL_UNSET,description=GOAL_UNSET,status=GOAL_UNSET,target_date=GOAL_UNSET,source_inbox_item_id=GOAL_UNSET):
        if isinstance(title, GoalUpdateContract):
            request = title
            title = request.title if "title" in request.provided else GOAL_UNSET
            description = request.description if "description" in request.provided else GOAL_UNSET
            status = request.status if "status" in request.provided else GOAL_UNSET
            target_date = request.target_date if "target_date" in request.provided else GOAL_UNSET
            source_inbox_item_id = request.source_inbox_item_id if "source_inbox_item_id" in request.provided else GOAL_UNSET
        return self._result(c,self.api.goal_service.update(c.actor.id,id,title,description,status,target_date,source_inbox_item_id))
    def lifecycle(self,c,id,action): return self._result(c,getattr(self.api.goal_service,action)(c.actor.id,id))
    def associate(self,c,goal_id,related_id,kind): return self._result(c,getattr(self.api.goal_service,"associate_"+kind)(c.actor.id,goal_id,related_id))
    def remove(self,c,goal_id,related_id,kind): return self.api.goal_service.remove_association(c.actor.id,goal_id,related_id,kind)
    def associated_ids(self,c,id): return self.api.goal_service.associated_ids(c.actor.id,id)
    def evidence(self,c,id,selected_date=None): return self.api.goal_service.evidence(c.actor.id,id,selected_date)
    def pause(self,c,id): return self.lifecycle(c,id,"pause")
    def resume(self,c,id): return self.lifecycle(c,id,"resume")
    def achieve(self,c,id): return self.lifecycle(c,id,"achieve")
    def abandon(self,c,id): return self.lifecycle(c,id,"abandon")
    def archive(self,c,id): return self.lifecycle(c,id,"archive")


class ProjectsNamespace:
    """Project lifecycle, task queries, progress, and next-action operations."""
    def __init__(self, api): self.api = api
    def _result(self,c,p):
        ids,total,done,open_count=self.api.project_service.progress(c.actor.id,p.id)
        return ProjectContract(p.id,p.title,p.description,p.status,p.next_action_task_id,p.source_inbox_item_id,p.created_at,p.updated_at,p.completed_at,p.archived_at,ids,total,done,open_count)
    def list(self,c): return [self._result(c,x) for x in self.api.project_service.list(c.actor.id)]
    def get(self,c,id): return self._result(c,self.api.project_service.get(c.actor.id,id))
    def create(self,c,title,description=None,source_inbox_item_id=None):
        if isinstance(title, ProjectCreateContract):
            request = title
            title, description, source_inbox_item_id = request.title, request.description, request.source_inbox_item_id
        return self._result(c,self.api.project_service.create(c.actor.id,title,description,source_inbox_item_id))
    def update(self,c,id,title=PROJECT_UNSET,description=PROJECT_UNSET,status=PROJECT_UNSET,source_inbox_item_id=PROJECT_UNSET):
        if isinstance(title, ProjectUpdateContract):
            request = title
            title = request.title if "title" in request.provided else PROJECT_UNSET
            description = request.description if "description" in request.provided else PROJECT_UNSET
            status = request.status if "status" in request.provided else PROJECT_UNSET
            source_inbox_item_id = request.source_inbox_item_id if "source_inbox_item_id" in request.provided else PROJECT_UNSET
        return self._result(c,self.api.project_service.update(c.actor.id,id,title,description,status,source_inbox_item_id))
    def lifecycle(self,c,id,action): return self._result(c,getattr(self.api.project_service,action)(c.actor.id,id))
    def tasks(self,c,id): return [_task(x) for x in self.api.project_service.task_list(c.actor.id,id)]
    def set_next_action(self,c,id,task_id): return self._result(c,self.api.project_service.set_next_action(c.actor.id,id,task_id))
    def clear_next_action(self,c,id): return self._result(c,self.api.project_service.clear_next_action(c.actor.id,id))
    def progress(self,c,id): return self.api.project_service.progress(c.actor.id,id)
    def pause(self,c,id): return self.lifecycle(c,id,"pause")
    def resume(self,c,id): return self.lifecycle(c,id,"resume")
    def complete(self,c,id): return self.lifecycle(c,id,"complete")
    def cancel(self,c,id): return self.lifecycle(c,id,"cancel")
    def archive(self,c,id): return self.lifecycle(c,id,"archive")


class TasksNamespace:
    """Task CRUD and lifecycle operations."""
    def __init__(self, api): self.api = api
    def list(self,c,status=None,project_id=None): return [_task(x) for x in self.api.task_service.list(c.actor.id,status,project_id)]
    def create(self,c,title,description=None,project_id=None,priority=None,due_date=None,is_today=False,source_inbox_item_id=None):
        from openipe.core.models.task import TaskPriority
        if isinstance(title, TaskCreateContract):
            request = title
            title, description, project_id, priority, due_date, is_today, source_inbox_item_id = request.title, request.description, request.project_id, request.priority, request.due_date, request.is_today, request.source_inbox_item_id
        return _task(self.api.task_service.create(c.actor.id,title,description,project_id,priority or TaskPriority.NORMAL,due_date,is_today,source_inbox_item_id))
    def get(self,c,id): return _task(self.api.task_service.get(c.actor.id,id))
    def update(self,c,id,*args,**fields):
        if args and isinstance(args[0], TaskUpdateContract):
            request = args[0]
            fields = {name: getattr(request, name) if name in request.provided else TASK_UNSET for name in ("title", "description", "project_id", "status", "priority", "due_date", "is_today", "source_inbox_item_id")}
        return _task(self.api.task_service.update(c.actor.id,id,**fields))
    def lifecycle(self,c,id,action): return _task(getattr(self.api.task_service,action)(c.actor.id,id))
    def complete(self,c,id): return self.lifecycle(c,id,"complete")
    def reopen(self,c,id): return self.lifecycle(c,id,"reopen")
    def cancel(self,c,id): return self.lifecycle(c,id,"cancel")


class HabitsNamespace:
    """Habit scheduling, activation, and check-in operations."""
    def __init__(self, api): self.api = api
    def list(self,c,active=None): return [_habit(x) for x in self.api.habit_service.list(c.actor.id,active)]
    def get(self,c,id): return _habit(self.api.habit_service.get(c.actor.id,id))
    def create(self,c,title,description=None,frequency_type=None,frequency_config=None,minimum_version=None,source_inbox_item_id=None):
        from openipe.core.models.habit import HabitFrequencyType
        if isinstance(title, HabitCreateContract):
            request = title
            title, description, frequency_type, frequency_config, minimum_version, source_inbox_item_id = request.title, request.description, request.frequency_type, request.frequency_config, request.minimum_version, request.source_inbox_item_id
        return _habit(self.api.habit_service.create(c.actor.id,title,description,frequency_type or HabitFrequencyType.DAILY,frequency_config or {},minimum_version,source_inbox_item_id))
    def update(self,c,id,*args,**fields):
        if args and isinstance(args[0], HabitUpdateContract):
            request = args[0]
            fields = {name: getattr(request, name) if name in request.provided else HABIT_UNSET for name in ("title", "description", "frequency_type", "frequency_config", "minimum_version", "active", "source_inbox_item_id")}
        return _habit(self.api.habit_service.update(c.actor.id,id,**fields))
    def lifecycle(self,c,id,action): return _habit(getattr(self.api.habit_service,action)(c.actor.id,id))
    def check_in(self,c,id,checkin_date,status=None,note=None):
        from openipe.core.models.habit import HabitCheckInStatus
        if isinstance(checkin_date, CheckInCreateContract):
            request = checkin_date
            checkin_date, status, note = request.date, request.status, request.note
        return _checkin(self.api.habit_service.check_in(c.actor.id,id,checkin_date,status or HabitCheckInStatus.COMPLETED,note))
    def get_check_in(self,c,id,checkin_date):
        item=self.api.habit_service.get_check_in(c.actor.id,id,checkin_date); return _checkin(item) if item else None
    def recent_check_ins(self,c,id,limit=30): return [_checkin(x) for x in self.api.habit_service.recent_check_ins(c.actor.id,id,limit)]
    def delete_check_in(self,c,id,checkin_date): return self.api.habit_service.delete_check_in(c.actor.id,id,checkin_date)
    def activate(self,c,id): return self.lifecycle(c,id,"activate")
    def deactivate(self,c,id): return self.lifecycle(c,id,"deactivate")
    def archive(self,c,id): return self.lifecycle(c,id,"archive")


class HabitStacksNamespace:
    """Habit stack membership, ordering, and date-aware progress operations."""
    def __init__(self, api): self.api = api
    def _result(self,c,s,selected_date=None):
        selected_date=selected_date or date.today(); done,scheduled=self.api.stack_service.progress(c.actor.id,s.id,selected_date)
        habits=[_habit(x) for x in self.api.stack_service.habits_in_stack(c.actor.id,s.id)]
        return HabitStackContract(s.id,s.name,s.description,s.position,s.active,s.created_at,s.updated_at,s.archived_at,done,scheduled,habits)
    def list(self,c,active=None,selected_date=None): return [self._result(c,x,selected_date) for x in self.api.stack_service.list(c.actor.id,active)]
    def get(self,c,id,selected_date=None): return self._result(c,self.api.stack_service.get(c.actor.id,id),selected_date)
    def create(self,c,name,description=None):
        if isinstance(name, StackCreateContract):
            request = name
            name, description = request.name, request.description
        return self._result(c,self.api.stack_service.create(c.actor.id,name,description))
    def update(self,c,id,name=STACK_UNSET,description=STACK_UNSET,active=STACK_UNSET):
        if isinstance(name, StackUpdateContract):
            request = name
            name = request.name if "name" in request.provided else STACK_UNSET
            description = request.description if "description" in request.provided else STACK_UNSET
            active = request.active if "active" in request.provided else STACK_UNSET
        return self._result(c,self.api.stack_service.update(c.actor.id,id,name,description,active))
    def lifecycle(self,c,id,action): return self._result(c,getattr(self.api.stack_service,action)(c.actor.id,id))
    def add_habit(self,c,stack_id,habit_id): self.api.stack_service.add_habit(c.actor.id,stack_id,habit_id); return self.get(c,stack_id)
    def remove_habit(self,c,stack_id,habit_id): self.api.stack_service.remove_habit(c.actor.id,stack_id,habit_id); return self.get(c,stack_id)
    def reorder_stacks(self,c,ids): return self.api.stack_service.reorder_stacks(c.actor.id,ids.ids if isinstance(ids, ReorderContract) else ids)
    def reorder_habits(self,c,stack_id,ids): return self.api.stack_service.reorder_habits(c.actor.id,stack_id,ids.ids if isinstance(ids, ReorderContract) else ids)
    def unstacked(self,c): return [_habit(x) for x in self.api.stack_service.unstacked_habits(c.actor.id)]
    def progress(self,c,id,selected_date=None): return self.api.stack_service.progress(c.actor.id,id,selected_date or date.today())
    def archive(self,c,id): return self.lifecycle(c,id,"archive")


class TodayNamespace:
    """Selected-date dashboard aggregation for REST and local clients."""
    def __init__(self, api): self.api = api
    def get(self,c,selected_date=None,include_completed=False):
        if isinstance(selected_date, TodayQueryContract):
            selected_date, include_completed = selected_date.selected_date, selected_date.include_completed
        # TodayService already returns transport-neutral primitives; freeze its
        # nested values into explicit contracts at this boundary.
        raw=self.api.today_service.get(c.actor.id,selected_date,include_completed)
        def goal(x): return TodayGoalContract(**x)
        def habit(x): return TodayHabitContract(x["id"],x["title"],x["minimum_version"],x["today_status"],x["position"],[goal(g) for g in x["goals"]])
        def task(x): return TodayTaskContract(x["id"],x["title"],x["description"],TodayProjectContract(**x["project"]) if x["project"] else None,[goal(g) for g in x["goals"]],x["priority"],x["due_date"],x["is_today"],x["status"],x["overdue"])
        stacks=[TodayStackContract(s["id"],s["name"],s["completed_count"],s["scheduled_count"],[habit(h) for h in s["habits"]]) for s in raw["habit_stacks"]]
        return TodayContract(raw["date"],[task(x) for x in raw["tasks"]],stacks,[habit(x) for x in raw["unstacked_habits"]],TodayCompletedContract([task(x) for x in raw["completed"]["tasks"]],[habit(x) for x in raw["completed"]["habits"]]))


class InternalAPI:
    """Explicit façade and sole public entry point for first-party clients."""
    def __init__(self, connection: sqlite3.Connection, settings: Settings):
        self.connection, self.settings = connection, settings
        self.auth_service = AuthService(connection, settings)
        self.inbox_service = InboxService(connection); self.goal_service = GoalService(connection)
        self.project_service = ProjectService(connection); self.task_service = TaskService(connection)
        self.habit_service = HabitService(connection); self.stack_service = HabitStackService(connection); self.today_service = TodayService(connection)
        self.auth = _PublicNamespace(AuthNamespace(self)); self.users = _PublicNamespace(UsersNamespace(self)); self.inbox = _PublicNamespace(InboxNamespace(self))
        self.goals = _PublicNamespace(GoalsNamespace(self)); self.projects = _PublicNamespace(ProjectsNamespace(self)); self.tasks = _PublicNamespace(TasksNamespace(self))
        self.habits = _PublicNamespace(HabitsNamespace(self)); self.habit_stacks = _PublicNamespace(HabitStacksNamespace(self)); self.today = _PublicNamespace(TodayNamespace(self))
    def authenticate(self, access_token: str) -> InternalContext:
        try:
            return InternalContext(self.auth_service.current_user(access_token))
        except AuthenticationError as error:
            raise InternalAuthenticationError(str(error)) from error

    def authorize_admin(self, context: InternalContext) -> InternalContext:
        if not isinstance(context, InternalContext):
            raise InvalidContextError("Authenticated context is required")
        if not context.actor.is_active or not context.actor.is_admin:
            raise InternalPermissionDeniedError("Administrator permission is required")
        return context


class _PublicNamespace:
    """Boundary proxy translating application errors for local clients."""
    def __init__(self, namespace):
        self._namespace = namespace

    def __getattr__(self, name):
        operation = getattr(self._namespace, name)
        if not callable(operation):
            return operation

        def invoke(*args, **kwargs):
            try:
                namespace_name = self._namespace.__class__.__name__
                unauthenticated = namespace_name == "AuthNamespace" and name in {
                    "initial_admin", "login", "logout"
                }
                if not unauthenticated and (
                    not args or not isinstance(args[0], InternalContext)
                ):
                    raise InvalidContextError("Authenticated context is required")
                return operation(*args, **kwargs)
            except AuthenticationError as error:
                raise InternalAuthenticationError(str(error)) from error
            except InactiveUserError as error:
                raise InternalInactiveUserError(str(error)) from error
            except PermissionDeniedError as error:
                raise InternalPermissionDeniedError(str(error)) from error
            except NotFoundError as error:
                raise InternalNotFoundError(str(error)) from error
            except ValidationError as error:
                raise InternalValidationError(str(error)) from error

        return invoke
