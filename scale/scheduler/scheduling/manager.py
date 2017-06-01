"""Defines the class that manages all scheduling"""
from __future__ import unicode_literals

from django.utils.timezone import now

from job.execution.manager import job_exe_mgr
from job.resources import NodeResources
from job.tasks.manager import task_mgr
from queue.job_exe import QueuedJobExecution
from queue.models import Queue
from scheduler.cleanup.manager import cleanup_mgr
from scheduler.node.manager import node_mgr
from scheduler.resources.manager import resource_mgr
from scheduler.scheduling.node import SchedulingNode
from scheduler.sync.job_type_manager import job_type_mgr
from scheduler.sync.scheduler_manager import scheduler_mgr

QUEUE_LIMIT = 500  # Maximum number of jobs to grab off of the queue at one time

# It is considered a resource shortage if a task waits this many generations without being scheduled
TASK_SHORTAGE_WAIT_COUNT = 10


class SchedulingManager(object):
    """This class manages all scheduling. This class is NOT thread-safe and should only be used within the scheduling
    thread.
    """

    def __init__(self):
        """Constructor
        """

        self._waiting_tasks = {}  # {Task ID: int}

    def perform_scheduling(self):
        """Organizes and analyzes the cluster resources, schedules new job executions, and launches tasks
        """

        when = now()

        nodes = self._prepare_nodes(when)

        job_types = job_type_mgr.get_job_types()
        job_type_resources = job_type_mgr.get_job_type_resources()
        running_job_exes = job_exe_mgr.get_ready_job_exes()

        fulfilled_nodes = self._schedule_waiting_tasks(nodes, running_job_exes, when)

        job_type_limits = self._calculate_job_type_limits(job_types, running_job_exes)

        # TODO: schedule new job_exes, including queries for job_exes and jobs

        # TODO: grab offers, do start_next_task() if resources are there, and launch tasks

    def _calculate_job_type_limits(self, job_types, running_job_exes):
        """Calculates and returns the available job type limits

        :param job_types: The dict of job type models stored by job type ID
        :type job_types: dict
        :param running_job_exes: The currently running job executions
        :type running_job_exes: [:class:`job.execution.job_exe.RunningJobExecution`]
        :returns: A dict where job type ID maps to the number of jobs of that type that can be scheduled. Missing job
            type IDs have no limit. Counts may be negative if the job type is scheduled above the limit.
        :rtype: dict
        """

        job_type_limits = {}
        for job_type in job_types.values():
            if job_type.max_scheduled:
                job_type_limits[job_type.id] = job_type.max_scheduled
        for running_job_exe in running_job_exes:
            if running_job_exe.job_type_id in job_type_limits:
                job_type_limits[running_job_exe.job_type_id] -= 1

    def _calculate_job_types_to_ignore(self, job_types, job_type_limits):
        """Calculates and returns the set of ID for job types to ignore on the queue

        :param job_types: The dict of job type models stored by job type ID
        :type job_types: dict
        :param job_type_limits: The dict of job type IDs mapping to job type limits
        :type job_type_limits: dict
        :returns: A set of the job type IDs to ignore
        :rtype: set
        """

        ignore_job_type_ids = set()

        # Ignore paused job types
        for job_type in job_types.values():
            if job_type.is_paused:
                ignore_job_type_ids.add(job_type.id)

        # Ignore job types that have reached their max scheduling limits
        for job_type_id in job_type_limits:
            if job_type_limits[job_type_id] < 1:
                ignore_job_type_ids.add(job_type_id)

        return ignore_job_type_ids

    def _prepare_nodes(self, when):
        """Prepares the nodes to use for scheduling

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The dict of scheduling nodes stored by node ID
        :rtype: dict
        """

        nodes = node_mgr.get_nodes()
        cleanup_mgr.update_nodes(nodes)

        tasks = task_mgr.get_all_tasks()
        tasks_by_agent_id = {}  # {Agent ID: Task}
        for task in tasks:
            if task.agent_id not in tasks_by_agent_id:
                tasks_by_agent_id[task.agent_id] = [task]
            else:
                tasks_by_agent_id[task.agent_id].append(task)

        agent_resources = resource_mgr.refresh_agent_resources(tasks, when)

        scheduling_nodes = {}  # {Node ID: SchedulingNode}
        for node in nodes:
            agent_id = node.agent_id   # Grab agent ID once since it could change while we are scheduling

            if agent_id in tasks_by_agent_id:
                node_tasks = tasks_by_agent_id[agent_id]
            else:
                node_tasks = []
            if agent_id in agent_resources:
                resource_set = agent_resources[agent_id]
            else:
                resource_set = None

            scheduling_node = SchedulingNode(agent_id, node, node_tasks, resource_set)
            scheduling_nodes[scheduling_node.node_id] = scheduling_node
        return scheduling_nodes

    def _schedule_new_job_exe(self, job_exe, nodes, job_type_resources):
        """Schedules the given job execution on the queue on one of the available nodes, if possible

        :param job_exe: The job execution to schedule
        :type job_exe: :class:`queue.job_exe.QueuedJobExecution`
        :param nodes: The dict of available scheduling nodes stored by node ID
        :type nodes: dict
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        :returns: True if scheduled, False otherwise
        :rtype: bool
        """

        # TODO: implement
        # TODO: use job type resources to find best node, also calculate node to reserve if needed
        return False

    def _schedule_new_job_exes(self, nodes, job_types, job_type_limits, job_type_resources):
        """Retrieves the top of the queue and schedules new job executions on available nodes as resources and limits
        allow

        :param nodes: The dict of scheduling nodes stored by node ID where every node has fulfilled all waiting tasks
        :type nodes: dict
        :param job_types: The dict of job type models stored by job type ID
        :type job_types: dict
        :param job_type_limits: The dict of job type IDs mapping to job type limits
        :type job_type_limits: dict
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        """

        # Can only use nodes that are ready for new job executions
        available_nodes = {}  # {Node ID: SchedulingNode}
        for node in nodes.values():
            if node.is_ready_for_new_job:
                available_nodes[node.node_id] = node

        ignore_job_type_ids = self._calculate_job_types_to_ignore(job_types, job_type_limits)

        # TODO: exception handling around all querying, in catch reset all scheduled new job exes in scheduling nodes
        for queue in Queue.objects.get_queue(scheduler_mgr.queue_mode(), ignore_job_type_ids)[:QUEUE_LIMIT]:
            # If there are no longer any available nodes, break
            if not nodes:
                break

            # Check limit for this execution's job type
            job_type_id = queue.job_type_id
            if job_type_id in job_type_limits and job_type_limits[job_type_id] < 1:
                continue

            # Try to schedule job execution and adjust job type limit if needed
            job_exe = QueuedJobExecution(queue)
            if self._schedule_new_job_exe(job_exe, available_nodes, job_type_resources):
                if job_type_id in job_type_limits:
                    job_type_limits[job_type_id] -= 1

        # TODO: do querying to schedule job_exes, somehow this all has to get back to the scheduling nodes so their
        # tasks can get created

    def _schedule_waiting_tasks(self, nodes, running_job_exes, when):
        """Schedules all waiting tasks for which there are sufficient resources and updates the resource manager with
        any resource shortages. All scheduling nodes that have fulfilled all of their waiting tasks will be returned so
        new job executions can be added to them.

        :param nodes: The dict of scheduling nodes stored by node ID
        :type nodes: dict
        :param running_job_exes: The list of currently running job executions
        :type running_job_exes: [:class:`job.execution.job_exe.RunningJobExecution`]
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The dict of scheduling nodes stored by node ID that have no more waiting tasks
        :rtype: dict
        """

        fulfilled_nodes = {}  # {Node ID: SchedulingNode}
        waiting_tasks = []

        # Schedule waiting node tasks first
        for node in nodes.values():
            has_waiting_tasks = node.accept_node_tasks(when, waiting_tasks)
            if node.is_ready_for_next_job_task and not has_waiting_tasks:
                # A node can only be fulfilled if it is able to run waiting tasks and it has no more waiting tasks
                fulfilled_nodes[node.node_id] = node

        # Schedule job executions already on the node waiting for their next task
        # TODO: fail job_exes with a "node lost" error if job_exe's node does not appear in the dict or is offline or
        # changed agent ID
        # TODO: fail job_exes if they are starving to get resources for their next task
        for running_job_exe in running_job_exes:
            if running_job_exe.node_id in nodes:
                node = nodes[running_job_exe.node_id]
                has_waiting_tasks = node.accept_job_exe_next_task(running_job_exe, waiting_tasks)
                if has_waiting_tasks and node.node_id in fulfilled_nodes:
                    # Node has tasks waiting for resources
                    del fulfilled_nodes[node.node.node_id]

        # Update waiting task counts and calculate shortages
        agent_shortages = {}  # {Agent ID: NodeResources}
        new_waiting_tasks = {}  # {Task ID: int}
        for task in waiting_tasks:
            if task.id in self._waiting_tasks:
                count = self._waiting_tasks[task.id] + 1
            else:
                count = 1
            new_waiting_tasks[task.id] = count
            if count >= TASK_SHORTAGE_WAIT_COUNT:
                # This task has waited too long for resources, generate a shortage
                if task.agent_id in agent_shortages:
                    agent_shortages[task.agent_id].add(task.get_resources())
                else:
                    resources = NodeResources()
                    resources.add(task.get_resources())
                    agent_shortages[task.agent_id] = resources
        self._waiting_tasks = new_waiting_tasks
        resource_mgr.set_agent_shortages(agent_shortages)

        return fulfilled_nodes
