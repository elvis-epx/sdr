#include "Task.h"

unsigned long int millis();

Task::Task(unsigned long int offset,
		TaskCallable* cb_target,
		unsigned long int (TaskCallable::*callback)(const Task*))
{
	this->offset = offset;
	this->timebase = 0;
	this->cb_target = cb_target;
	this->callback = callback;
}

Task::~Task()
{
	this->cb_target = 0;
	this->cb_callback = 0;
	this->timebase = 0;
}

void Task::set_timebase(unsigned long int now)
{
	this->timebase = now;
}

bool Task::should_run(unsigned long int now) const
{
	return this->timebase > 0 && 
		(this->timebase + this->offset) <= now;
}

bool Task::cancelled() const
{
	return this->timebase <= 0;
}

bool Task::run()
{
	// callback returns new timeout (which could be random)
	this->timeout = cb_target->callback(this);
	// task cancelled by default, rescheduled by task mgr
	this->timebase = 0;
	return this->timeout > 0;
}


TaskManager::TaskManager() {}

TaskManager::~TaskManager() {}

void TaskManager::schedule(Task* task)
{
	Ptr<Task> etask = task;
	tasks.push_back(etask);
	etask->set_timebase(millis());
}

void TaskManager::cancel(const Task *task)
{
	for (unsigned int i = 0 ; i < tasks.size(); ++i) {
		if (tasks[i]->id() == task) {
			tasks.remov(i);
			break;
		}
	}
}

bool TaskManager::run(unsigned long int now)
{
	bool dirty = false;

	for (unsigned int i = 0 ; i < tasks.size(); ++i) {
		Ptr<Task> t = tasks[i];
		if (t->should_run(now)) {
			bool stay = t->run();
			if (stay) {
				// reschedule
				t->set_timebase(millis());
			} else {
				// task list must be pruned
				dirty = true;
			}
		}
	}

	while (dirty) {
		dirty = false;
		for (unsigned int i = 0 ; i < tasks.size(); ++i) {
			Ptr<Task> t = tasks[i];
			if (t->cancelled()) {
				tasks.remov(i);
				dirty = true;
				break;
			}
		}
	}
}
